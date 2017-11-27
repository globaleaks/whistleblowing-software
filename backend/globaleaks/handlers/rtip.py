# -*- coding: utf-8
#
# rtip
# ****
#
# Contains all the logic for handling tip related operations, for the
# receiver side. These classes are executed in the /rtip/* URI PATH

import os
import string
from storm.expr import In

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.custodian import serialize_identityaccessrequest, db_get_identityaccessrequest_list
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.submission import serialize_usertip
from globaleaks.models import serializers
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import Settings
from globaleaks.security import directory_traversal_check
from globaleaks.state import State
from globaleaks.utils.utility import log, get_expiration, datetime_now, datetime_never, \
    datetime_to_ISO8601


def receiver_serialize_rfile(store, tid, rfile):
    ifile = store.find(models.InternalFile,
                       models.InternalFile.id == models.ReceiverFile.internalfile_id,
                       models.ReceiverFile.id == rfile.id,
                       tid=tid).one()

    if rfile.status != 'unavailable':
        ret_dict = {
            'id': rfile.id,
            'internalfile_id': ifile.id,
            'status': rfile.status,
            'href': "/rtip/" + rfile.receivertip_id + "/download/" + rfile.id,
            # if the ReceiverFile has encrypted status, we append ".pgp" to the filename, to avoid mistake on Receiver side.
            'name': ("%s.pgp" % ifile.name) if rfile.status == u'encrypted' else ifile.name,
            'content_type': ifile.content_type,
            'creation_date': datetime_to_ISO8601(ifile.creation_date),
            'size': rfile.size,
            'downloads': rfile.downloads
        }

    else:  # == 'unavailable' in this case internal file metadata is returned.
        ret_dict = {
            'id': rfile.id,
            'internalfile_id': ifile.id,
            'status': 'unavailable',
            'href': "",
            'name': ifile.name,
            'content_type': ifile.content_type,
            'creation_date': datetime_to_ISO8601(ifile.creation_date),
            'size': int(ifile.size),
            'downloads': rfile.downloads
        }

    return ret_dict


def receiver_serialize_wbfile(store, wbfile):
    rtip = models.db_get(store, models.ReceiverTip, id=wbfile.receivertip_id, tid=wbfile.tid)

    return {
        'id': wbfile.id,
        'creation_date': datetime_to_ISO8601(wbfile.creation_date),
        'name': wbfile.name,
        'description': wbfile.description,
        'size': wbfile.size,
        'content_type': wbfile.content_type,
        'downloads': wbfile.downloads,
        'author': rtip.receiver_id
    }


def serialize_comment(store, comment):
    author = 'Recipient'

    if comment.type == 'whistleblower':
        author = 'Whistleblower'
    elif comment.author_id is not None:
        author = store.find(models.User,
                            models.User.id == comment.author_id,
                            tid=comment.tid).one().public_name

    return {
        'id': comment.id,
        'author': author,
        'type': comment.type,
        'creation_date': datetime_to_ISO8601(comment.creation_date),
        'content': comment.content
    }


def serialize_message(store, message):
    if message.type == 'whistleblower':
        author = 'Whistleblower'
    else:
        author = store.find(models.User,
                            models.User.id == models.ReceiverTip.receiver_id,
                            models.ReceiverTip.id == models.Message.receivertip_id,
                            models.Message.id == message.id,
                            tid=message.tid).one().public_name

    return {
        'id': message.id,
        'author': author,
        'type': message.type,
        'creation_date': datetime_to_ISO8601(message.creation_date),
        'content': message.content
    }


def serialize_rtip(store, rtip, itip, language):
    user_id = rtip.receiver_id

    ret = serialize_usertip(store, rtip, itip, language)

    ret['id'] = rtip.id
    ret['receiver_id'] = user_id
    ret['label'] = rtip.label
    ret['comments'] = db_get_itip_comment_list(store, itip.tid, itip)
    ret['messages'] = db_get_itip_message_list(store, itip.tid, rtip)
    ret['rfiles'] = db_receiver_get_rfile_list(store, itip.tid, rtip.id)
    ret['wbfiles'] = db_receiver_get_wbfile_list(store, itip.tid, itip.id)
    ret['iars'] = db_get_identityaccessrequest_list(store, itip.tid, rtip.id, language)
    ret['enable_notifications'] = bool(rtip.enable_notifications)

    return ret


def db_access_rtip(store, tid, user_id, rtip_id):
    return models.db_get(store, 
                         (models.ReceiverTip, models.InternalTip),
                         models.ReceiverTip.id == rtip_id,
                         models.ReceiverTip.receiver_id == user_id,
                         models.ReceiverTip.internaltip_id == models.InternalTip.id,
                         models.ReceiverTip.tid == tid)


def db_access_wbfile(store, tid, user_id, wbfile_id):
    itips = store.find(models.InternalTip,
                       models.InternalTip.id == models.ReceiverTip.internaltip_id,
                       models.ReceiverTip.receiver_id == user_id,
                       tid=tid)

    itips_ids = [itip.id for itip in itips]

    wbfile = store.find(models.WhistleblowerFile,
                        models.WhistleblowerFile.id == wbfile_id,
                        models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                        In(models.ReceiverTip.internaltip_id, itips_ids),
                        tid=tid).one()

    if not wbfile:
        raise errors.WBFileIdNotFound

    return wbfile


def db_receiver_get_rfile_list(store, tid, rtip_id):
    rfiles = store.find(models.ReceiverFile,
                        models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                        models.ReceiverTip.id == rtip_id,
                        tid=tid)

    return [receiver_serialize_rfile(store, tid, rfile) for rfile in rfiles]


def db_receiver_get_wbfile_list(store, tid, itip_id):
    rtips = store.find(models.ReceiverTip, models.ReceiverTip.internaltip_id == itip_id, tid=tid)
    rtips_ids = [rt.id for rt in rtips]
    wbfiles = store.find(models.WhistleblowerFile, In(models.WhistleblowerFile.receivertip_id, rtips_ids), tid=tid)

    return [receiver_serialize_wbfile(store, wbfile) for wbfile in wbfiles]


@transact
def register_wbfile_on_db(store, tid, rtip_id, uploaded_file):
    rtip, itip = store.find((models.ReceiverTip, models.InternalTip),
                             models.ReceiverTip.id == rtip_id,
                             models.InternalTip.id == models.ReceiverTip.internaltip_id,
                             models.ReceiverTip.tid == tid).one()

    itip.update_date = rtip.last_access = datetime_now()

    new_file = models.WhistleblowerFile()
    new_file.tid = tid
    new_file.name = uploaded_file['name']
    new_file.description = uploaded_file['description']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.receivertip_id = rtip_id
    new_file.file_path = uploaded_file['path']

    store.add(new_file)

    return serializers.serialize_wbfile(store, tid, new_file)


@transact
def receiver_get_rfile_list(store, tid, rtip_id):
    return db_receiver_get_rfile_list(store, tid, rtip_id)


def db_get_rtip(store, tid, user_id, rtip_id, language):
    rtip, itip = db_access_rtip(store, tid, user_id, rtip_id)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    return serialize_rtip(store, rtip, itip, language)


def db_mark_file_for_secure_deletion(store, relpath):
    abspath = os.path.join(Settings.attachments_path, relpath)

    if not os.path.isfile(abspath):
        log.err("Tried to permanently delete a non existent file: %s" % abspath)
        return

    secure_file_delete = models.SecureFileDelete()
    secure_file_delete.filepath = abspath
    store.add(secure_file_delete)


def db_delete_itip_files(store, itip_id):
    log.debug("Removing files associated to InternalTip %s" % itip_id)

    for ifile in store.find(models.InternalFile, internaltip_id=itip_id):
        log.debug("Marking internalfile %s for secure deletion" % ifile.file_path)

        db_mark_file_for_secure_deletion(store, ifile.file_path)

        for rfile in store.find(models.ReceiverFile, models.ReceiverFile.internalfile_id == ifile.id):
            # The following code must be bypassed if rfile.file_path == ifile.filepath,
            # this mean that is referenced the plaintext file instead having E2E.
            if rfile.file_path == ifile.file_path:
                continue

            log.debug("Marking receiverfile %s for secure deletion" % rfile.file_path)

            db_mark_file_for_secure_deletion(store, rfile.file_path)

    for wbfile in store.find(models.WhistleblowerFile,
                             models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                             models.ReceiverTip.internaltip_id == itip_id):
        log.debug("Marking whistleblowerfile %s for secure deletion" % wbfile.file_path)
        db_mark_file_for_secure_deletion(store, wbfile.file_path)


def db_delete_itip(store, itip):
    log.debug("Removing InternalTip %s" % itip.id)

    db_delete_itip_files(store, itip.id)

    store.remove(itip)

    if store.find(models.InternalTip, models.InternalTip.questionnaire_hash == itip.questionnaire_hash).count() == 0:
        store.find(models.ArchivedSchema, models.ArchivedSchema.hash == itip.questionnaire_hash).remove()


def db_postpone_expiration_date(store, tid, itip):
    context = store.find((models.Context), id=itip.context_id, tid=tid).one()

    if context.tip_timetolive > -1:
        itip.expiration_date = get_expiration(context.tip_timetolive)
    else:
        itip.expiration_date = datetime_never()


@transact
def delete_rtip(store, tid, user_id, rtip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated property.
    """
    rtip, itip = db_access_rtip(store, tid, user_id, rtip_id)

    receiver = models.db_get(store, models.Receiver, id=rtip.receiver_id, tid=tid)

    if not (State.tenant_cache[tid].can_delete_submission or
            receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    db_delete_itip(store, itip)


@transact
def postpone_expiration_date(store, tid, user_id, rtip_id):
    rtip, itip = db_access_rtip(store, tid, user_id, rtip_id)

    receiver = models.db_get(store, models.Receiver, id=rtip.receiver_id, tid=tid)

    if not (State.tenant_cache[tid].can_postpone_expiration or
            receiver.can_postpone_expiration):
        raise errors.ExtendTipLifeNotEnabled

    db_postpone_expiration_date(store, tid, itip)


@transact
def set_internaltip_variable(store, tid, user_id, rtip_id, key, value):
    rtip, itip = db_access_rtip(store, tid, user_id, rtip_id)

    receiver = models.db_get(store, models.Receiver, id=rtip.receiver_id, tid=tid)

    if not (State.tenant_cache[tid].can_grant_permissions or
            receiver.can_grant_permissions):
        raise errors.ForbiddenOperation

    setattr(itip, key, value)


@transact
def set_receivertip_variable(store, tid, user_id, rtip_id, key, value):
    rtip, _ = db_access_rtip(store, tid, user_id, rtip_id)
    setattr(rtip, key, value)


@transact
def get_rtip(store, tid, user_id, rtip_id, language):
    return db_get_rtip(store, tid, user_id, rtip_id, language)


def db_get_itip_comment_list(store, tid, itip):
    return [serialize_comment(store, comment) for comment in store.find(models.Comment, internaltip_id=itip.id, tid=tid)]


@transact
def create_identityaccessrequest(store, tid, user_id, rtip_id, request):
    rtip, _ = db_access_rtip(store, tid, user_id, rtip_id)

    iar = models.IdentityAccessRequest()
    iar.tid = tid
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id
    store.add(iar)

    return serialize_identityaccessrequest(store, tid, iar)


@transact
def create_comment(store, tid, user_id, rtip_id, request):
    rtip, itip = db_access_rtip(store, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    comment = models.Comment()
    comment.tid = tid
    comment.content = request['content']
    comment.internaltip_id = itip.id
    comment.type = u'receiver'
    comment.author_id = rtip.receiver_id
    store.add(comment)

    return serialize_comment(store, comment)


def db_get_itip_message_list(store, tid, rtip):
    return [serialize_message(store, message) for message in store.find(models.Message, receivertip_id=rtip.id, tid=tid)]


@transact
def create_message(store, tid, user_id, rtip_id, request):
    rtip, itip = db_access_rtip(store, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    msg = models.Message()
    msg.tid = tid
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.type = u'receiver'
    store.add(msg)

    return serialize_message(store, msg)


@transact
def delete_wbfile(store, tid, user_id, file_id):
    wbfile = db_access_wbfile(store, tid, user_id, file_id)
    db_mark_file_for_secure_deletion(store, wbfile.file_path)
    store.remove(wbfile)


class RTipInstance(OperationHandler):
    """
    This interface exposes the Receiver's Tip
    """
    check_roles = 'receiver'

    def get(self, tip_id):
        """
        Parameters: None
        Response: actorsTipDesc
        Errors: InvalidAuthentication

        tip_id can be a valid tip_id (Receiver case) or a random one (because is
        ignored, only authenticated user with whistleblower token can access to
        the wbtip, this is why tip_is is not checked if self.is_whistleblower)

        This method is decorated as @BaseHandler.unauthenticated because in the handler
        the various cases are managed differently.
        """
        return get_rtip(self.request.tid, self.current_user.user_id, tip_id, self.request.language)

    def operation_descriptors(self):
        return {
          'postpone_expiration': (RTipInstance.postpone_expiration, None),
          'set': (RTipInstance.set_tip_val,
                  {'key': '^(enable_two_way_comments|enable_two_way_messages|enable_attachments|enable_notifications)$',
                   'value': bool}),
          'set_label': (RTipInstance.set_label, {'value': unicode})
        }


    def set_tip_val(self, req_args, tip_id, *args, **kwargs):
        value = req_args['value']
        key = req_args['key']

        if key == 'enable_notifications':
            return set_receivertip_variable(self.request.tid, self.current_user.user_id, tip_id, key, value)

        return set_internaltip_variable(self.request.tid, self.current_user.user_id, tip_id, key, value)

    def postpone_expiration(self, _, tip_id, *args, **kwargs):
        return postpone_expiration_date(self.request.tid, self.current_user.user_id, tip_id)

    def set_label(self, req_args, tip_id, *args, **kwargs):
        return set_receivertip_variable(self.request.tid, self.current_user.user_id, tip_id, 'label', req_args['value'])

    def delete(self, tip_id):
        """
        Response: None
        Errors: ForbiddenOperation

        delete: remove the Internaltip and all the associated data
        """
        return delete_rtip(self.request.tid, self.current_user.user_id, tip_id)


class RTipCommentCollection(BaseHandler):
    """
    Interface use to write rtip comments
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidAuthentication, InvalidInputFormat, ModelNotFound
        """
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_comment(self.request.tid, self.current_user.user_id, tip_id, request)


class ReceiverMsgCollection(BaseHandler):
    """
    Interface use to write rtip messages
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        """
        Request: CommentDesc
        Response: CommentDesc
        Errors: InvalidAuthentication, InvalidInputFormat, ModelNotFound
        """
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_message(self.request.tid, self.current_user.user_id, tip_id, request)


class WhistleblowerFileHandler(BaseHandler):
    """
    Receiver interface to upload a file intended for the whistleblower
    """
    check_roles = 'receiver'
    upload_handler = True

    @transact
    def can_perform_action(self, store, tid, tip_id, filename):
        rtip, _ = db_access_rtip(store, tid, self.current_user.user_id, tip_id)

        enable_rc_to_wb_files = store.find(models.Context.enable_rc_to_wb_files,
                                           models.Context.id == models.InternalTip.context_id,
                                           models.InternalTip.id == rtip.internaltip_id,
                                           models.Context.tid == tid).one()

        if not enable_rc_to_wb_files:
            raise errors.ForbiddenOperation()

    @inlineCallbacks
    def post(self, tip_id):
        """
        Errors: ModelNotFound, ForbiddenOperation
        """
        yield self.can_perform_action(self.request.tid, tip_id, self.uploaded_file['name'])

        rtip = yield get_rtip(self.request.tid, self.current_user.user_id, tip_id, self.request.language)

        # First: dump the file in the filesystem
        filename = string.split(os.path.basename(self.uploaded_file['path']), '.aes')[0] + '.plain'

        dst = os.path.join(Settings.attachments_path, filename)

        directory_traversal_check(Settings.attachments_path, dst)

        yield threads.deferToThread(self.write_upload_plaintext_to_disk, dst)

        self.uploaded_file['creation_date'] = datetime_now()
        self.uploaded_file['submission'] = False

        yield register_wbfile_on_db(self.request.tid, rtip['id'], self.uploaded_file)

        log.debug("Recorded new WhistleblowerFile %s", self.uploaded_file['name'])


class WBFileHandler(BaseHandler):
    """
    This class is used in both RTip and WBTip to define a base for respective handlers
    """
    check_roles = 'receiver'

    def user_can_access(self, store, tid, wbfile):
        raise NotImplementedError("This class defines the user_can_access interface.")

    def access_wbfile(self, store, wbfile):
        pass

    @transact
    def download_wbfile(self, store, tid, user_id, file_id):
        wbfile = store.find(models.WhistleblowerFile,
                            models.WhistleblowerFile.id == file_id,
                            tid=tid).one()

        if wbfile is None or not self.user_can_access(store, tid, wbfile):
            raise errors.FileIdNotFound

        self.access_wbfile(store, wbfile)

        return serializers.serialize_wbfile(store, tid, wbfile)

    @inlineCallbacks
    def get(self, wbfile_id):
        wbfile = yield self.download_wbfile(self.request.tid, self.current_user.user_id, wbfile_id)

        filelocation = os.path.join(Settings.attachments_path, wbfile['path'])

        directory_traversal_check(Settings.attachments_path, filelocation)

        yield self.force_file_download(wbfile['name'], filelocation)


class RTipWBFileHandler(WBFileHandler):
    """
    This handler lets the recipient download and delete wbfiles, which are files
    intended for delivery to the whistleblower.
    """
    check_roles = 'receiver'

    def user_can_access(self, store, tid, wbfile):
        internaltip_id = store.find(models.ReceiverTip.internaltip_id,
                                    models.ReceiverTip.id == wbfile.receivertip_id,
                                    models.ReceiverTip.tid == tid).one()

        return self.current_user.user_id in store.find(models.ReceiverTip.receiver_id,
                                                       models.ReceiverTip.internaltip_id == internaltip_id,
                                                       models.ReceiverTip.tid == tid)

    def delete(self, file_id):
        """
        This interface allow the recipient to set the description of a WhistleblowerFile
        """
        return delete_wbfile(self.request.tid, self.current_user.user_id, file_id)


class ReceiverFileDownload(BaseHandler):
    """
    This handler exposes rfiles for download.
    """
    check_roles = 'receiver'

    @transact
    def download_rfile(self, store, tid, user_id, file_id):
        rfile, receiver_id = store.find((models.ReceiverFile, models.ReceiverTip.receiver_id),
                                        models.ReceiverFile.id == file_id,
                                        models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                                        models.ReceiverTip.receiver_id == user_id,
                                        models.ReceiverTip.tid == tid).one()

        if not rfile:
            raise errors.FileIdNotFound

        log.debug("Download of file %s by receiver %s (%d)" %
                  (rfile.internalfile_id, receiver_id, rfile.downloads))

        rfile.downloads += 1

        return serializers.serialize_rfile(store, tid, rfile)

    @inlineCallbacks
    def get(self, rfile_id):
        rfile = yield self.download_rfile(self.request.tid, self.current_user.user_id, rfile_id)

        filelocation = os.path.join(Settings.attachments_path, rfile['path'])

        directory_traversal_check(Settings.attachments_path, filelocation)

        yield self.force_file_download(rfile['name'], filelocation)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    This interface allow to perform identity access requests.
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        """
        Request: IdentityAccessRequestDesc
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.content.read(), requests.ReceiverIdentityAccessRequestDesc)

        return create_identityaccessrequest(self.request.tid,
                                            self.current_user.user_id,
                                            tip_id,
                                            request)
