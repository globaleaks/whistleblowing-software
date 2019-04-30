# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for receivers (rtip)
import base64
import os

from six import text_type
from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.custodian import serialize_identityaccessrequest
from globaleaks.handlers.file import db_mark_file_for_secure_deletion
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.submission import serialize_usertip, decrypt_tip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.models import serializers
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.crypto import GCE
from globaleaks.utils.fs import directory_traversal_check
from globaleaks.utils.log import log
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import get_expiration, datetime_now, datetime_never, datetime_to_ISO8601


def db_update_submission_status(session, user_id, itip, submission_status_id, submission_substatus_id):
    itip.status = submission_status_id
    itip.substatus = submission_substatus_id or None

    submission_status_change = models.SubmissionStatusChange()
    submission_status_change.internaltip_id = itip.id
    submission_status_change.status = submission_status_id
    submission_status_change.substatus = submission_substatus_id or None
    submission_status_change.changed_by = user_id

    session.add(submission_status_change)


def receiver_serialize_rfile(session, rfile):
    ifile = session.query(models.InternalFile) \
                   .filter(models.InternalFile.id == rfile.internalfile_id).one()

    if rfile.status == 'unavailable':
        return {
            'id': rfile.id,
            'internalfile_id': ifile.id,
            'status': 'unavailable',
            'href': "",
            'name': ifile.name,
            'content_type': ifile.content_type,
            'creation_date': datetime_to_ISO8601(ifile.creation_date),
            'size': ifile.size,
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
        'size': ifile.size,
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
        _author = session.query(models.User) \
                         .filter(models.User.id == comment.author_id).one_or_none()

        if _author is not None:
            author = _author.name

    return {
        'id': comment.id,
        'author': author,
        'type': comment.type,
        'creation_date': datetime_to_ISO8601(comment.creation_date),
        'content': comment.content
    }


def serialize_message(session, message):
    receiver_involved = session.query(models.User) \
                               .filter(models.User.id == models.ReceiverTip.receiver_id,
                                       models.ReceiverTip.id == models.Message.receivertip_id,
                                       models.Message.id == message.id).one()

    if message.type == 'whistleblower':
        author = 'Whistleblower'
    else:
        author = receiver_involved.name

    return {
        'id': message.id,
        'author': author,
        'type': message.type,
        'creation_date': datetime_to_ISO8601(message.creation_date),
        'content': message.content,
        'receiver_involved': receiver_involved.id
    }


def serialize_rtip(session, rtip, itip, language):
    user_id = rtip.receiver_id

    ret = serialize_usertip(session, rtip, itip, language)

    if(not rtip.can_access_whistleblower_identity and 'whistleblower_identity' in ret['data']):
        del ret['data']['whistleblower_identity']

    ret['id'] = rtip.id
    ret['receiver_id'] = user_id
    ret['label'] = rtip.label
    ret['comments'] = db_get_itip_comment_list(session, itip.id)
    ret['messages'] = db_get_itip_message_list(session, rtip.id)
    ret['rfiles'] = db_receiver_get_rfile_list(session, rtip.id)
    ret['wbfiles'] = db_receiver_get_wbfile_list(session, itip.id)
    ret['iars'] = db_get_rtip_identityaccessrequest_list(session, rtip.id)
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


def db_receiver_get_rfile_list(session, rtip_id):
    rfiles = session.query(models.ReceiverFile) \
                    .filter(models.ReceiverFile.receivertip_id == rtip_id)

    return [receiver_serialize_rfile(session, rfile) for rfile in rfiles]


def db_receiver_get_wbfile_list(session, itip_id):
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
    new_file.filename = uploaded_file['filename']

    session.add(new_file)

    return serializers.serialize_wbfile(session, tid, new_file)


@transact
def receiver_get_rfile_list(session, rtip_id):
    return db_receiver_get_rfile_list(session, rtip_id)


def db_set_itip_open_if_new(session, tid, user_id, itip):
    new_status_id = session.query(models.SubmissionStatus.id) \
                          .filter(models.SubmissionStatus.tid == tid,
                                  models.SubmissionStatus.system_usage == 'new').one()[0]

    if new_status_id == itip.status:
        open_status_id = session.query(models.SubmissionStatus.id) \
                              .filter(models.SubmissionStatus.tid == tid,
                                      models.SubmissionStatus.system_usage == 'opened').one()[0]

        db_update_submission_status(session, user_id, itip, open_status_id, '')


def db_get_rtip(session, tid, user_id, rtip_id, language):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    db_set_itip_open_if_new(session, tid, user_id, itip)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    return serialize_rtip(session, rtip, itip, language), rtip.crypto_tip_prv_key


def db_delete_itips_files(session, itips_ids):
    ifiles_ids = set()
    files_names = set()

    if itips_ids:
        for ifile_id, ifile_filename in session.query(models.InternalFile.id, models.InternalFile.filename) \
                                               .filter(models.InternalFile.internaltip_id.in_(itips_ids)):
            ifiles_ids.add(ifile_id)
            files_names.add(ifile_filename)

        for wbfile_filename in session.query(models.WhistleblowerFile.filename) \
                                      .filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                                              models.ReceiverTip.internaltip_id.in_(itips_ids)):
            files_names.add(wbfile_filename[0])

    if ifiles_ids:
        for rfile_filename in session.query(models.ReceiverFile.filename) \
                                     .filter(models.ReceiverFile.internalfile_id.in_(ifiles_ids)):
            files_names.add(rfile_filename[0])

    for filename in files_names:
        db_mark_file_for_secure_deletion(session, Settings.attachments_path, filename)


def db_delete_itips(session, itips_ids):
    db_delete_itips_files(session, itips_ids)

    session.query(models.InternalTip) \
           .filter(models.InternalTip.id.in_(itips_ids)).delete(synchronize_session='fetch')


def db_delete_itip(session, itip):
    db_delete_itips(session, [itip.id])


def db_postpone_expiration_date(session, tid, itip):
    context = session.query(models.Context).filter(models.Context.id == itip.context_id, models.Context.tid == tid).one()

    if context.tip_timetolive > 0:
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

    receiver = models.db_get(session, models.User, models.User.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_delete_submission or
            receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    db_delete_itip(session, itip)


@transact
def postpone_expiration_date(session, tid, user_id, rtip_id):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    receiver = models.db_get(session, models.User, models.User.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_postpone_expiration or
            receiver.can_postpone_expiration):
        raise errors.ForbiddenOperation

    db_postpone_expiration_date(session, tid, itip)


@transact
def set_internaltip_variable(session, tid, user_id, rtip_id, key, value):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    receiver = models.db_get(session, models.User, models.User.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_grant_permissions or
            receiver.can_grant_permissions):
        raise errors.ForbiddenOperation

    setattr(itip, key, value)


@transact
def set_receivertip_variable(session, tid, user_id, rtip_id, key, value):
    rtip, _ = db_access_rtip(session, tid, user_id, rtip_id)
    setattr(rtip, key, value)


@transact
def update_tip_submission_status(session, tid, user_id, rtip_id, submission_status_uuid, submission_substatus_uuid):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    db_update_submission_status(session, user_id, itip, submission_status_uuid, submission_substatus_uuid)


@transact
def get_rtip(session, tid, user_id, rtip_id, language):
    return db_get_rtip(session, tid, user_id, rtip_id, language)


def db_get_itip_comment_list(session, itip_id):
    return [serialize_comment(session, comment) for comment in session.query(models.Comment).filter(models.Comment.internaltip_id == itip_id)]


def db_create_identityaccessrequest_notifications(session, tid, itip, rtip, iar):
    users = session.query(models.User).filter(models.User.role == u'custodian', models.User.notification == True)
    for user in users:
        node = db_admin_serialize_node(session, tid, user.language)
        context = session.query(models.Context).filter(models.Context.id == itip.context_id, models.Context.tid == tid).one()

        data = {
            'type': 'identity_access_request'
        }

        data['user'] = user_serialize_user(session, user, user.language)
        data['tip'] = serialize_rtip(session, rtip, itip, user.language)
        data['context'] = admin_serialize_context(session, context, user.language)
        data['iar'] = serialize_identityaccessrequest(session, iar)
        data['node'] = db_admin_serialize_node(session, tid, user.language)

        if data['node']['mode'] != u'whistleblowing.it':
            data['notification'] = db_get_notification(session, tid, user.language)
        else:
            data['notification'] = db_get_notification(session, 1, user.language)

        subject, body = Templating().get_mail_subject_and_body(data)

        session.add(models.Mail({
            'address': data['user']['mail_address'],
            'subject': subject,
            'body': body,
            'tid': tid
        }))


@transact
def create_identityaccessrequest(session, tid, user_id, rtip_id, request):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    iar = models.IdentityAccessRequest()
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id
    session.add(iar)
    session.flush()

    db_create_identityaccessrequest_notifications(session, tid, itip, rtip, iar)

    return serialize_identityaccessrequest(session, iar)


@transact
def create_comment(session, tid, user_id, user_key, rtip_id, content):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    comment = models.Comment()
    comment.internaltip_id = itip.id
    comment.type = u'receiver'
    comment.author_id = rtip.receiver_id

    if itip.crypto_tip_pub_key:
        comment.content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()
    else:
        comment.content = content

    session.add(comment)
    session.flush()

    ret = serialize_comment(session, comment)
    ret['content'] = content

    return ret


def db_get_itip_message_list(session, rtip_id):
    return [serialize_message(session, message) for message in session.query(models.Message).filter(models.Message.receivertip_id == rtip_id)]


def db_get_rtip_identityaccessrequest_list(session, rtip_id):
    return [serialize_identityaccessrequest(session, iar) for iar in session.query(models.IdentityAccessRequest).filter(models.IdentityAccessRequest.receivertip_id == rtip_id)]


@transact
def create_message(session, tid, user_id, user_key, rtip_id, content):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    msg = models.Message()
    msg.receivertip_id = rtip.id
    msg.type = u'receiver'

    if itip.crypto_tip_pub_key:
        msg.content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()
    else:
        msg.content = content

    session.add(msg)
    session.flush()

    ret = serialize_message(session, msg)
    ret['content'] = content
    return ret


@transact
def delete_wbfile(session, tid, user_id, file_id):
    wbfile = db_access_wbfile(session, tid, user_id, file_id)
    db_mark_file_for_secure_deletion(session, Settings.attachments_path, wbfile.filename)
    session.delete(wbfile)


class RTipInstance(OperationHandler):
    """
    This interface exposes the Receiver's Tip
    """
    check_roles = 'receiver'

    @inlineCallbacks
    def get(self, tip_id):
        tip, crypto_tip_prv_key = yield get_rtip(self.request.tid, self.current_user.user_id, tip_id, self.request.language)

        if State.tenant_cache[self.request.tid].encryption and crypto_tip_prv_key:
            tip = yield deferToThread(decrypt_tip, self.current_user.cc, crypto_tip_prv_key, tip)

        returnValue(tip)

    def operation_descriptors(self):
        return {
          'postpone_expiration': (RTipInstance.postpone_expiration, None),
          'set': (RTipInstance.set_tip_val,
                  {'key': '^(enable_two_way_comments|enable_two_way_messages|enable_attachments|enable_notifications)$',
                   'value': bool}),
          'update_label': (RTipInstance.update_label, {'value': text_type}),
          'update_status': (RTipInstance.update_submission_status, {'status': text_type,
                                                                    'substatus': text_type})
        }

    def set_tip_val(self, req_args, tip_id, *args, **kwargs):
        value = req_args['value']
        key = req_args['key']

        if key == 'enable_notifications':
            return set_receivertip_variable(self.request.tid, self.current_user.user_id, tip_id, key, value)

        return set_internaltip_variable(self.request.tid, self.current_user.user_id, tip_id, key, value)

    def postpone_expiration(self, _, tip_id, *args, **kwargs):
        return postpone_expiration_date(self.request.tid, self.current_user.user_id, tip_id)

    def update_label(self, req_args, tip_id, *args, **kwargs):
        return set_receivertip_variable(self.request.tid, self.current_user.user_id, tip_id, 'label', req_args['value'])

    def update_submission_status(self, req_args, tip_id, *args, **kwargs):
        return update_tip_submission_status(self.request.tid, self.current_user.user_id, tip_id,
                                            req_args['status'], req_args['substatus'])

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

        return create_comment(self.request.tid, self.current_user.user_id, self.current_user.cc, tip_id, request['content'])


class ReceiverMsgCollection(BaseHandler):
    """
    Interface use to write rtip messages
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_message(self.request.tid, self.current_user.user_id, self.current_user.cc, tip_id, request['content'])


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

        yield register_wbfile_on_db(self.request.tid, tip_id, self.uploaded_file)

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
        x = session.query(models.WhistleblowerFile, models.WhistleblowerTip) \
                   .filter(models.WhistleblowerFile.id == file_id,
                           models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                           models.ReceiverTip.internaltip_id == models.WhistleblowerTip.id).one_or_none()

        if x is None or not self.user_can_access(session, tid, x[0]):
            raise errors.ModelNotFound(models.WhistleblowerFile)

        wbfile, wbtip = x[0], x[1]

        self.access_wbfile(session, wbfile)

        return serializers.serialize_wbfile(session, tid, wbfile), wbtip.crypto_tip_prv_key

    @inlineCallbacks
    def get(self, wbfile_id):
        wbfile, tip_prv_key = yield self.download_wbfile(self.request.tid, self.current_user.id, wbfile_id)

        filelocation = os.path.join(Settings.attachments_path, wbfile['filename'])

        directory_traversal_check(Settings.attachments_path, filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.current_user.cc, tip_prv_key)
            fo = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, filelocation)
            yield self.write_file_as_download_fo(wbfile['name'], fo)
        else:
            yield self.write_file_as_download(wbfile['name'], filelocation)


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

        users_ids = [x[0] for x in session.query(models.ReceiverTip.receiver_id)
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
        rfile, rtip = session.query(models.ReceiverFile, models.ReceiverTip) \
                             .filter(models.ReceiverFile.id == file_id,
                                     models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                                     models.ReceiverTip.receiver_id == user_id,
                                     models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                     models.InternalTip.tid == tid).one()

        if not rfile:
            raise errors.ModelNotFound(models.ReceiverFile)

        log.debug("Download of file %s by receiver %s (%d)" %
                  (rfile.internalfile_id, rtip.receiver_id, rfile.downloads))

        rfile.last_access = datetime_now()
        rfile.downloads += 1

        return serializers.serialize_rfile(session, tid, rfile), rtip.crypto_tip_prv_key

    @inlineCallbacks
    def get(self, rfile_id):
        rfile, tip_prv_key = yield self.download_rfile(self.request.tid, self.current_user.user_id, rfile_id)

        filelocation = os.path.join(Settings.attachments_path, rfile['filename'])

        directory_traversal_check(Settings.attachments_path, filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.current_user.cc, tip_prv_key)
            fo = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, filelocation)
            yield self.write_file_as_download_fo(rfile['name'], fo)
        else:
            yield self.write_file_as_download(rfile['name'], filelocation)


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
