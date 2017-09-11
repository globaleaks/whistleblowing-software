# -*- coding: UTF-8
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
from globaleaks.handlers.base import BaseHandler, \
    directory_traversal_check, write_upload_plaintext_to_disk
from globaleaks.handlers.custodian import serialize_identityaccessrequest
from globaleaks.handlers.submission import serialize_usertip, db_get_internaltip_from_usertip
from globaleaks.models import serializers
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, get_expiration, datetime_now, datetime_never, \
    datetime_to_ISO8601, datetime_to_pretty_str


def receiver_serialize_rfile(store, rfile):
    ifile = store.find(models.InternalFile,
                       models.InternalFile.id == models.ReceiverFile.internalfile_id,
                       models.ReceiverFile.id == rfile.id).one()

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
    rtip = models.db_get(store, models.ReceiverTip,id=wbfile.receivertip_id)

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
    if comment.type == 'whistleblower':
        author = 'Whistleblower'
    elif comment.author_id is not None:
        author = store.find(models.User,
                            models.User.id == comment.author_id).one().public_name
    else:
        author = 'Recipient'

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
                            models.Message.id == message.id).one().public_name

    return {
        'id': message.id,
        'author': author,
        'type': message.type,
        'creation_date': datetime_to_ISO8601(message.creation_date),
        'content': message.content
    }


def serialize_rtip(store, rtip, language):
    user_id = rtip.receiver_id

    ret = serialize_usertip(store, rtip, language)

    internaltip = db_get_internaltip_from_usertip(store, rtip)

    ret['id'] = rtip.id
    ret['receiver_id'] = user_id
    ret['label'] = rtip.label
    ret['comments'] = db_get_itip_comment_list(store, internaltip)
    ret['messages'] = db_get_itip_message_list(store, rtip)
    ret['rfiles'] = db_receiver_get_rfile_list(store, rtip.id)
    ret['wbfiles'] = db_receiver_get_wbfile_list(store, rtip.internaltip_id)
    ret['iars'] = db_get_identityaccessrequest_list(store, rtip.id, language)
    ret['enable_notifications'] = bool(rtip.enable_notifications)

    return ret


def db_access_rtip(store, user_id, rtip_id):
    return models.db_get(store, models.ReceiverTip, id=unicode(rtip_id), receiver_id= user_id)


def db_access_wbfile(store, user_id, wbfile_id):
    itips = store.find(models.InternalTip,
                       models.InternalTip.id == models.ReceiverTip.internaltip_id,
                       models.ReceiverTip.receiver_id == user_id)

    itips_ids = [itip.id for itip in itips]

    wbfile = store.find(models.WhistleblowerFile,
                        models.WhistleblowerFile.id == unicode(wbfile_id),
                        models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                        In(models.ReceiverTip.internaltip_id, itips_ids)).one()

    if not wbfile:
        raise errors.WBFileIdNotFound

    return wbfile


def db_receiver_get_rfile_list(store, rtip_id):
    rfiles = store.find(models.ReceiverFile,
                        models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                        models.ReceiverTip.id == rtip_id)

    return [receiver_serialize_rfile(store, rfile) for rfile in rfiles]


def db_receiver_get_wbfile_list(store, itip_id):
    rtips = store.find(models.ReceiverTip, models.ReceiverTip.internaltip_id == itip_id)
    rtips_ids = [rt.id for rt in rtips]
    wbfiles = store.find(models.WhistleblowerFile, In(models.WhistleblowerFile.receivertip_id, rtips_ids))

    return [receiver_serialize_wbfile(store, wbfile) for wbfile in wbfiles]


@transact
def register_wbfile_on_db(store, rtip_id, uploaded_file):
    rtip, internaltip = store.find((models.ReceiverTip, models.InternalTip),
                                   models.ReceiverTip.id == rtip_id,
                                   models.InternalTip.id == models.ReceiverTip.internaltip_id).one()

    internaltip.update_date = rtip.last_access = datetime_now()

    new_file = models.WhistleblowerFile()
    new_file.name = uploaded_file['name']
    new_file.description = uploaded_file['description']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.receivertip_id = rtip_id
    new_file.file_path = uploaded_file['path']

    store.add(new_file)

    return serializers.serialize_wbfile(store, new_file)


@transact
def receiver_get_rfile_list(store, rtip_id):
    return db_receiver_get_rfile_list(store, rtip_id)


def db_get_rtip(store, user_id, rtip_id, language):
    rtip = db_access_rtip(store, user_id, rtip_id)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    return serialize_rtip(store, rtip, language)


def db_mark_file_for_secure_deletion(store, relpath):
    abspath = os.path.join(GLSettings.submission_path, relpath)
    if os.path.isfile(abspath):
        secure_file_delete = models.SecureFileDelete()
        secure_file_delete.filepath = abspath
        store.add(secure_file_delete)
    else:
        log.err("Tried to permanently delete a non existent file: %s" % abspath)


def db_delete_itip_files(store, itip):
    log.debug("Removing files associated to InternalTip %s" % itip.id)
    for ifile in store.find(models.InternalFile,
                            models.InternalFile.internaltip_id == itip.id):
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
                             models.ReceiverTip.internaltip_id == itip.id):
        log.debug("Marking whistleblowerfile %s for secure deletion" % wbfile.file_path)
        db_mark_file_for_secure_deletion(store, wbfile.file_path)


def db_delete_itip(store, itip):
    log.debug("Removing InternalTip %s" % itip.id)

    db_delete_itip_files(store, itip)

    store.remove(itip)

    if store.find(models.InternalTip, models.InternalTip.questionnaire_hash == itip.questionnaire_hash).count() == 0:
        store.find(models.ArchivedSchema, models.ArchivedSchema.hash == itip.questionnaire_hash).remove()


def db_delete_itips(store, itips):
    for itip in itips:
        db_delete_itip(store, itip)


def db_delete_rtip(store, rtip):
    return db_delete_itip(store, db_get_internaltip_from_usertip(store, rtip))


def db_postpone_expiration_date(store, rtip):
    internaltip, context = store.find((models.InternalTip, models.Context),
                                      models.InternalTip.id == rtip.internaltip_id,
                                      models.Context.id == models.InternalTip.context_id).one()

    if context.tip_timetolive > -1:
        internaltip.expiration_date = get_expiration(context.tip_timetolive)
    else:
        internaltip.expiration_date = datetime_never()


@transact
def delete_rtip(store, user_id, rtip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated property.
    """
    rtip = db_access_rtip(store, user_id, rtip_id)

    receiver = models.db_get(store, models.Receiver, id=rtip.receiver_id)

    if not (GLSettings.memory_copy.can_delete_submission or
            receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    db_delete_rtip(store, rtip)


@transact
def postpone_expiration_date(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    receiver = models.db_get(store, models.Receiver, id=rtip.receiver_id)

    if not (GLSettings.memory_copy.can_postpone_expiration or
            receiver.can_postpone_expiration):
        raise errors.ExtendTipLifeNotEnabled

    db_postpone_expiration_date(store, rtip)


@transact
def set_internaltip_variable(store, user_id, rtip_id, key, value):
    rtip = db_access_rtip(store, user_id, rtip_id)

    receiver = models.db_get(store, models.Receiver, id=rtip.receiver_id)

    if not (GLSettings.memory_copy.can_grant_permissions or
            receiver.can_grant_permissions):
        raise errors.ForbiddenOperation

    internaltip = db_get_internaltip_from_usertip(store, rtip)

    setattr(internaltip, key, value)


@transact
def set_receivertip_variable(store, user_id, rtip_id, key, value):
    rtip = db_access_rtip(store, user_id, rtip_id)
    setattr(rtip, key, value)


@transact
def get_rtip(store, user_id, rtip_id, language):
    return db_get_rtip(store, user_id, rtip_id, language)


def db_get_itip_comment_list(store, itip):
    return [serialize_comment(store, comment) for comment in store.find(models.Comment, internaltip_id=itip.id)]


@transact
def create_identityaccessrequest(store, user_id, rtip_id, request):
    rtip = db_access_rtip(store, user_id, rtip_id)

    iar = models.IdentityAccessRequest()
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id
    store.add(iar)

    return serialize_identityaccessrequest(store, iar)


@transact
def create_comment(store, user_id, rtip_id, request):
    rtip = db_access_rtip(store, user_id, rtip_id)

    internaltip = db_get_internaltip_from_usertip(store, rtip)

    internaltip.update_date = rtip.last_access = datetime_now()

    comment = models.Comment()
    comment.content = request['content']
    comment.internaltip_id = rtip.internaltip_id
    comment.type = u'receiver'
    comment.author_id = rtip.receiver_id
    store.add(comment)

    return serialize_comment(store, comment)


def db_get_itip_message_list(store, rtip):
    return [serialize_message(store, message) for message in store.find(models.Message, models.Message.receivertip_id == rtip.id)]


@transact
def create_message(store, user_id, rtip_id, request):
    rtip = db_access_rtip(store, user_id, rtip_id)

    internaltip = db_get_internaltip_from_usertip(store, rtip)

    internaltip.update_date = rtip.last_access = datetime_now()

    msg = models.Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.type = u'receiver'
    store.add(msg)

    return serialize_message(store, msg)


@transact
def delete_wbfile(store, user_id, file_id):
    wbfile = db_access_wbfile(store, user_id, file_id)
    db_mark_file_for_secure_deletion(store, wbfile.file_path)
    store.remove(wbfile)


def db_get_identityaccessrequest_list(store, rtip_id, language):
    return [serialize_identityaccessrequest(store, iar) for iar in store.find(models.IdentityAccessRequest, receivertip_id=rtip_id)]


class RTipInstance(BaseHandler):
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
        return get_rtip(self.current_user.user_id, tip_id, self.request.language)

    def put(self, tip_id):
        """
        Some special operations that manipulate a Tip are handled here
        """
        request = self.validate_message(self.request.content.read(), requests.TipOpsDesc)

        if request['operation'] == 'postpone':
            return postpone_expiration_date(self.current_user.user_id, tip_id)
        elif request['operation'] == 'set':
            key = request['args']['key']
            value = request['args']['value']
            internal_var_lst = ['enable_two_way_comments',
                                'enable_two_way_messages',
                                'enable_attachments']
            if ((key == 'label'                and isinstance(value, unicode)) or
                (key == 'enable_notifications' and isinstance(value, bool))):
                return set_receivertip_variable(self.current_user.user_id, tip_id, key, value)
            elif key in internal_var_lst and isinstance(value, bool):
                # Elements of internal_var_lst are not stored in the receiver's tip table
                return set_internaltip_variable(self.current_user.user_id, tip_id, key, value)

    def delete(self, tip_id):
        """
        Response: None
        Errors: ForbiddenOperation

        delete: remove the Internaltip and all the associated data
        """
        return delete_rtip(self.current_user.user_id, tip_id)


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

        return create_comment(self.current_user.user_id, tip_id, request)


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

        return create_message(self.current_user.user_id, tip_id, request)


class WhistleblowerFileHandler(BaseHandler):
    """
    Receiver interface to upload a file intended for the whistleblower
    """
    check_roles = 'receiver'

    @transact
    def can_perform_action(self, store, tip_id, filename):
        rtip = db_access_rtip(store, self.current_user.user_id, tip_id)

        enable_rc_to_wb_files = store.find(models.Context.enable_rc_to_wb_files,
                                           models.Context.id == models.InternalTip.context_id,
                                           models.InternalTip.id == rtip.internaltip_id).one()

        if not enable_rc_to_wb_files:
            raise errors.ForbiddenOperation()

    @inlineCallbacks
    def post(self, tip_id):
        """
        Errors: ModelNotFound, ForbiddenOperation
        """
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        yield self.can_perform_action(tip_id, uploaded_file['name'])

        rtip = yield get_rtip(self.current_user.user_id, tip_id, self.request.language)

        try:
            # First: dump the file in the filesystem
            filename = string.split(os.path.basename(uploaded_file['path']), '.aes')[0] + '.plain'

            dst = os.path.join(GLSettings.submission_path, filename)

            directory_traversal_check(GLSettings.submission_path, dst)

            uploaded_file = yield threads.deferToThread(write_upload_plaintext_to_disk, uploaded_file, dst)
        except Exception as excep:
            log.err("Unable to save a file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")

        uploaded_file['creation_date'] = datetime_now()
        uploaded_file['submission'] = False

        yield register_wbfile_on_db(rtip['id'], uploaded_file)

        log.debug("Recorded new WhistleblowerFile %s", uploaded_file['name'])


class WhistleblowerFileInstanceHandler(BaseHandler):
    """
    This class is used in both RTip and WBTip to define a base for respective handlers
    """
    check_roles = 'receiver'

    def user_can_access(self, store, wbfile):
        raise NotImplementedError("This class defines the user_can_access interface.")

    def access_wbfile(self, store, wbfile):
        pass

    @transact
    def download_wbfile(self, store, user_id, file_id):
        wbfile = store.find(models.WhistleblowerFile,
                            models.WhistleblowerFile.id == file_id).one()

        if wbfile is None or not self.user_can_access(store, wbfile):
            raise errors.FileIdNotFound

        self.access_wbfile(store, wbfile)

        return serializers.serialize_wbfile(store, wbfile)

    @inlineCallbacks
    def get(self, wbfile_id):
        wbfile = yield self.download_wbfile(self.current_user.user_id, wbfile_id)

        filelocation = os.path.join(GLSettings.submission_path, wbfile['path'])

        directory_traversal_check(GLSettings.submission_path, filelocation)

        yield self.force_file_download(wbfile['name'], filelocation)


class RTipWBFileInstanceHandler(WhistleblowerFileInstanceHandler):
    """
    This handler lets the recipient download and delete wbfiles, which are files
    intended for delivery to the whistleblower.
    """
    check_roles = 'receiver'

    def user_can_access(self, store, wbfile):
        internaltip_id = store.find(models.ReceiverTip.internaltip_id,
                                    models.ReceiverTip.id == wbfile.receivertip_id).one()

        return self.current_user.user_id in store.find(models.ReceiverTip.receiver_id,
                                                       models.ReceiverTip.internaltip_id == internaltip_id)

    def delete(self, file_id):
        """
        This interface allow the recipient to set the description of a WhistleblowerFile
        """
        return delete_wbfile(self.current_user.user_id, file_id)


class ReceiverFileDownload(BaseHandler):
    """
    This handler exposes rfiles for download.
    """
    check_roles = 'receiver'

    @transact
    def download_rfile(self, store, user_id, file_id):
        rfile, receiver_id = store.find((models.ReceiverFile, models.ReceiverTip.receiver_id),
                                        models.ReceiverFile.id == file_id,
                                        models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                                        models.ReceiverTip.receiver_id == user_id).one()

        if not rfile:
            raise errors.FileIdNotFound

        log.debug("Download of file %s by receiver %s (%d)" %
                  (rfile.internalfile_id, receiver_id, rfile.downloads))

        rfile.downloads += 1

        return serializers.serialize_rfile(store, rfile)

    @inlineCallbacks
    def get(self, rfile_id):
        rfile = yield self.download_rfile(self.current_user.user_id, rfile_id)

        filelocation = os.path.join(GLSettings.submission_path, rfile['path'])

        directory_traversal_check(GLSettings.submission_path, filelocation)

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

        return create_identityaccessrequest(self.current_user.user_id,
                                            tip_id,
                                            request)
