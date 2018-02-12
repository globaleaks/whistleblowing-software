# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for receivers (rtip)
import os
import string

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
from globaleaks.utils.security import directory_traversal_check
from globaleaks.state import State
from globaleaks.utils.utility import log, get_expiration, datetime_now, datetime_never, \
    datetime_to_ISO8601


def receiver_serialize_rfile(session, rfile):
    ifile = session.query(models.InternalFile) \
                   .filter(models.InternalFile.id == models.ReceiverFile.internalfile_id,
                           models.ReceiverFile.id == rfile.id).one()

    if rfile.status == 'unavailable':
        return {
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

    return {
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


def receiver_serialize_wbfile(session, wbfile):
    rtip = models.db_get(session, models.ReceiverTip, models.ReceiverTip.id == wbfile.receivertip_id)

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


def serialize_comment(session, comment):
    author = 'Recipient'

    if comment.type == 'whistleblower':
        author = 'Whistleblower'
    elif comment.author_id is not None:
        author = session.query(models.User) \
                        .filter(models.User.id == comment.author_id).one().name

    return {
        'id': comment.id,
        'author': author,
        'type': comment.type,
        'creation_date': datetime_to_ISO8601(comment.creation_date),
        'content': comment.content
    }


def serialize_message(session, message):
    if message.type == 'whistleblower':
        author = 'Whistleblower'
    else:
        author = session.query(models.User) \
                        .filter(models.User.id == models.ReceiverTip.receiver_id,
                                models.ReceiverTip.id == models.Message.receivertip_id,
                                models.Message.id == message.id).one().name

    return {
        'id': message.id,
        'author': author,
        'type': message.type,
        'creation_date': datetime_to_ISO8601(message.creation_date),
        'content': message.content
    }


def serialize_rtip(session, rtip, itip, language):
    user_id = rtip.receiver_id

    ret = serialize_usertip(session, rtip, itip, language)

    ret['id'] = rtip.id
    ret['receiver_id'] = user_id
    ret['label'] = rtip.label
    ret['comments'] = db_get_itip_comment_list(session, itip.tid, itip)
    ret['messages'] = db_get_itip_message_list(session, itip.tid, rtip)
    ret['rfiles'] = db_receiver_get_rfile_list(session, itip.tid, rtip.id)
    ret['wbfiles'] = db_receiver_get_wbfile_list(session, itip.tid, itip.id)
    ret['iars'] = db_get_identityaccessrequest_list(session, itip.tid, rtip.id)
    ret['enable_notifications'] = bool(rtip.enable_notifications)

    return ret


def db_access_rtip(session, tid, user_id, rtip_id):
    return models.db_get(session,
                         (models.ReceiverTip, models.InternalTip),
                         models.ReceiverTip.id == rtip_id,
                         models.ReceiverTip.receiver_id == user_id,
                         models.ReceiverTip.internaltip_id == models.InternalTip.id,
                         models.InternalTip.tid == tid)


def db_access_wbfile(session, tid, user_id, wbfile_id):
    itips = session.query(models.InternalTip) \
                   .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                           models.ReceiverTip.receiver_id == user_id,
                           models.InternalTip.tid == tid)

    itips_ids = [itip.id for itip in itips]

    wbfile = session.query(models.WhistleblowerFile) \
                    .filter(models.WhistleblowerFile.id == wbfile_id,
                            models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                            models.ReceiverTip.internaltip_id.in_(itips_ids),
                            models.InternalTip.tid == tid).one()

    if not wbfile:
        raise errors.ModelNotFound(models.WhistleblowerFile)

    return wbfile


def db_receiver_get_rfile_list(session, tid, rtip_id):
    rfiles = session.query(models.ReceiverFile) \
                    .filter(models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                            models.ReceiverTip.id == rtip_id,
                            models.ReceiverTip.internaltip_id == models.InternalTip.id,
                            models.InternalTip.tid == tid)

    return [receiver_serialize_rfile(session, rfile) for rfile in rfiles]


def db_receiver_get_wbfile_list(session, tid, itip_id):
    rtips = session.query(models.ReceiverTip) \
                   .filter(models.ReceiverTip.internaltip_id == itip_id)

    rtips_ids = [rt.id for rt in rtips]

    wbfiles = []
    if rtips_ids:
        wbfiles = session.query(models.WhistleblowerFile) \
                        .filter(models.WhistleblowerFile.receivertip_id.in_(rtips_ids))

    return [receiver_serialize_wbfile(session, wbfile) for wbfile in wbfiles]


@transact
def register_wbfile_on_db(session, tid, rtip_id, uploaded_file):
    rtip, itip = session.query(models.ReceiverTip, models.InternalTip) \
                        .filter(models.ReceiverTip.id == rtip_id,
                                models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                models.InternalTip.tid == tid).one()

    itip.update_date = rtip.last_access = datetime_now()

    new_file = models.WhistleblowerFile()
    new_file.name = uploaded_file['name']
    new_file.description = uploaded_file['description']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.receivertip_id = rtip_id
    new_file.file_path = uploaded_file['path']

    session.add(new_file)

    return serializers.serialize_wbfile(session, tid, new_file)


@transact
def receiver_get_rfile_list(session, tid, rtip_id):
    return db_receiver_get_rfile_list(session, tid, rtip_id)


def db_get_rtip(session, tid, user_id, rtip_id, language):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    return serialize_rtip(session, rtip, itip, language)


def db_mark_file_for_secure_deletion(session, relpath):
    abspath = os.path.join(Settings.attachments_path, relpath)

    if not os.path.isfile(abspath):
        log.err("Tried to permanently delete a non existent file: %s" % abspath)
        return

    secure_file_delete = models.SecureFileDelete()
    secure_file_delete.filepath = abspath
    session.add(secure_file_delete)


def db_delete_itips_files(session, itips_ids):
    files_paths = set()
    ifiles_ids = set()

    if itips_ids:
        for ifile in session.query(models.InternalFile) \
                            .filter(models.InternalFile.internaltip_id.in_(itips_ids)):
            files_paths.add(ifile.file_path)
            ifiles_ids.add(ifile.id)

    if ifiles_ids:
        for rfile in session.query(models.ReceiverFile) \
                            .filter(models.ReceiverFile.internalfile_id.in_(list(ifiles_ids))):
            files_paths.add(rfile.file_path)

    if ifiles_ids:
        for wbfile in session.query(models.WhistleblowerFile) \
                             .filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                                     models.ReceiverTip.internaltip_id.in_(list(ifiles_ids))):
            files_paths.add(wbfile.file_path)

    for file_path in files_paths:
        db_mark_file_for_secure_deletion(session, file_path)


def db_delete_itips(session, itips_ids):
    db_delete_itips_files(session, itips_ids)

    session.query(models.InternalTip) \
         .filter(models.InternalTip.id.in_(itips_ids)).delete(synchronize_session='fetch')

def db_delete_itip(session, itip):
    db_delete_itips(session, [itip.id])

def db_postpone_expiration_date(session, tid, itip):
    context = session.query(models.Context).filter(models.Context.id == itip.context_id, models.Context.tid == tid).one()

    if context.tip_timetolive > -1:
        itip.expiration_date = get_expiration(context.tip_timetolive)
    else:
        itip.expiration_date = datetime_never()


@transact
def delete_rtip(session, tid, user_id, rtip_id):
    """
    Delete internalTip is possible only to Receiver with
    the dedicated property.
    """
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    receiver = models.db_get(session, models.Receiver, models.Receiver.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_delete_submission or
            receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    db_delete_itip(session, itip)


@transact
def postpone_expiration_date(session, tid, user_id, rtip_id):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    receiver = models.db_get(session, models.Receiver, models.Receiver.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_postpone_expiration or
            receiver.can_postpone_expiration):
        raise errors.ForbiddenOperation

    db_postpone_expiration_date(session, tid, itip)


@transact
def set_internaltip_variable(session, tid, user_id, rtip_id, key, value):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    receiver = models.db_get(session, models.Receiver, models.Receiver.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_grant_permissions or
            receiver.can_grant_permissions):
        raise errors.ForbiddenOperation

    setattr(itip, key, value)


@transact
def set_receivertip_variable(session, tid, user_id, rtip_id, key, value):
    rtip, _ = db_access_rtip(session, tid, user_id, rtip_id)
    setattr(rtip, key, value)


@transact
def get_rtip(session, tid, user_id, rtip_id, language):
    return db_get_rtip(session, tid, user_id, rtip_id, language)


def db_get_itip_comment_list(session, tid, itip):
    return [serialize_comment(session, comment) for comment in session.query(models.Comment).filter(models.Comment.internaltip_id == itip.id)]


@transact
def create_identityaccessrequest(session, tid, user_id, rtip_id, request):
    rtip, _ = db_access_rtip(session, tid, user_id, rtip_id)

    iar = models.IdentityAccessRequest()
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id
    session.add(iar)
    session.flush()

    return serialize_identityaccessrequest(session, tid, iar)


@transact
def create_comment(session, tid, user_id, rtip_id, request):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    comment = models.Comment()
    comment.content = request['content']
    comment.internaltip_id = itip.id
    comment.type = u'receiver'
    comment.author_id = rtip.receiver_id
    session.add(comment)
    session.flush()

    return serialize_comment(session, comment)


def db_get_itip_message_list(session, tid, rtip):
    return [serialize_message(session, message) for message in session.query(models.Message).filter(models.Message.receivertip_id == rtip.id)]


@transact
def create_message(session, tid, user_id, rtip_id, request):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    msg = models.Message()
    msg.content = request['content']
    msg.receivertip_id = rtip.id
    msg.type = u'receiver'
    session.add(msg)
    session.flush()

    return serialize_message(session, msg)


@transact
def delete_wbfile(session, tid, user_id, file_id):
    wbfile = db_access_wbfile(session, tid, user_id, file_id)
    db_mark_file_for_secure_deletion(session, wbfile.file_path)
    session.delete(wbfile)


class RTipInstance(OperationHandler):
    """
    This interface exposes the Receiver's Tip
    """
    check_roles = 'receiver'

    def get(self, tip_id):
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
        Remove the Internaltip and all the associated data
        """
        return delete_rtip(self.request.tid, self.current_user.user_id, tip_id)


class RTipCommentCollection(BaseHandler):
    """
    Interface use to write rtip comments
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_comment(self.request.tid, self.current_user.user_id, tip_id, request)


class ReceiverMsgCollection(BaseHandler):
    """
    Interface use to write rtip messages
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_message(self.request.tid, self.current_user.user_id, tip_id, request)


class WhistleblowerFileHandler(BaseHandler):
    """
    Receiver interface to upload a file intended for the whistleblower
    """
    check_roles = 'receiver'
    upload_handler = True

    @transact
    def can_perform_action(self, session, tid, tip_id, filename):
        rtip, _ = db_access_rtip(session, tid, self.current_user.user_id, tip_id)

        enable_rc_to_wb_files = session.query(models.Context.enable_rc_to_wb_files) \
                                       .filter(models.Context.id == models.InternalTip.context_id,
                                               models.InternalTip.id == rtip.internaltip_id,
                                               models.Context.tid == tid).one()

        if not enable_rc_to_wb_files:
            raise errors.ForbiddenOperation()

    @inlineCallbacks
    def post(self, tip_id):
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

    def user_can_access(self, session, tid, wbfile):
        raise NotImplementedError("This class defines the user_can_access interface.")

    def access_wbfile(self, session, wbfile):
        pass

    @transact
    def download_wbfile(self, session, tid, user_id, file_id):
        wbfile = session.query(models.WhistleblowerFile) \
                        .filter(models.WhistleblowerFile.id == file_id).one_or_none()

        if wbfile is None or not self.user_can_access(session, tid, wbfile):
            raise errors.ModelNotFound(models.WhistleblowerFile)

        self.access_wbfile(session, wbfile)

        return serializers.serialize_wbfile(session, tid, wbfile)

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

    def user_can_access(self, session, tid, wbfile):
        internaltip_id = session.query(models.ReceiverTip.internaltip_id) \
                                .filter(models.ReceiverTip.id == wbfile.receivertip_id,
                                        models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                        models.InternalTip.tid == tid).one()[0]

        users_ids = [x[0] for x in session.query(models.ReceiverTip.receiver_id) \
                                          .filter(models.ReceiverTip.internaltip_id == internaltip_id,
                                                  models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                                  models.InternalTip.tid == tid)]

        return self.current_user.user_id in users_ids

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
    def download_rfile(self, session, tid, user_id, file_id):
        rfile, receiver_id = session.query(models.ReceiverFile, models.ReceiverTip.receiver_id) \
                                    .filter(models.ReceiverFile.id == file_id,
                                            models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                                            models.ReceiverTip.receiver_id == user_id,
                                            models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                            models.InternalTip.tid == tid).one()

        if not rfile:
            raise errors.ModelNotFound(models.ReceiverFile)

        log.debug("Download of file %s by receiver %s (%d)" %
                  (rfile.internalfile_id, receiver_id, rfile.downloads))

        rfile.last_access = datetime_now()
        rfile.downloads += 1

        return serializers.serialize_rfile(session, tid, rfile)

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
        request = self.validate_message(self.request.content.read(), requests.ReceiverIdentityAccessRequestDesc)

        return create_identityaccessrequest(self.request.tid,
                                            self.current_user.user_id,
                                            tip_id,
                                            request)
