# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for receivers (rtip)
import base64
import os

from datetime import datetime, timedelta

from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.submission import db_create_receivertip, decrypt_tip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.models import serializers, Context
from globaleaks.orm import db_get, db_del, db_log, transact, tw
from globaleaks.rest import errors, requests
from globaleaks.state import State
from globaleaks.utils.crypto import GCE
from globaleaks.utils.fs import directory_traversal_check
from globaleaks.utils.log import log
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import get_expiration, datetime_now, datetime_null, datetime_never


def db_tip_grant_notification(session, user):
    """
    Transaction for the creation of notifications related to grant of access to report
    :param session: An ORM session
    :param user: A user to which send the notification
    """
    data = {
        'type': 'tip_access'
    }

    data['user'] = user_serialize_user(session, user, user.language)
    data['node'] = db_admin_serialize_node(session, user.tid, user.language)

    if data['node']['mode'] == 'default':
        data['notification'] = db_get_notification(session, user.tid, user.language)
    else:
        data['notification'] = db_get_notification(session, 1, user.language)

    subject, body = Templating().get_mail_subject_and_body(data)

    session.add(models.Mail({
        'address': data['user']['mail_address'],
        'subject': subject,
        'body': body,
        'tid': user.tid
    }))


def db_grant_tip_access(session, tid, user_id, user_cc, rtip_id, receiver_id):
    """
    Transaction for granting a user access to a report

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param user_cc: A user crypto key
    :param rtip_id: A rtip_id of the rtip on which perform the operation
    :param receiver_id: A user ID of the the user to which grant access to the report
    """
    receiver, itip, rtip = session.query(models.User, models.InternalTip, models.ReceiverTip) \
                                  .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                          models.ReceiverTip.id == rtip_id,
                                          models.User.id == models.ReceiverTip.receiver_id).one()
    if user_id == receiver_id or not receiver.can_grant_access_to_reports:
        raise errors.ForbiddenOperation


    existing = session.query(models.ReceiverTip).filter(models.ReceiverTip.receiver_id == receiver_id,
                                                        models.ReceiverTip.internaltip_id == itip.id).one_or_none()

    if existing:
        return

    new_receiver = db_get(session,
                          models.User,
                          models.User.id == receiver_id)

    if itip.crypto_tip_pub_key and not new_receiver.crypto_pub_key:
        # Access to encrypted submissions could be granted only if the recipient has performed first login
        return

    if itip.crypto_tip_pub_key:
        _tip_key = GCE.asymmetric_decrypt(user_cc, base64.b64decode(rtip.crypto_tip_prv_key))
        _tip_key = GCE.asymmetric_encrypt(new_receiver.crypto_pub_key, _tip_key)
        _files_key = GCE.asymmetric_decrypt(user_cc, base64.b64decode(rtip.crypto_files_prv_key))
        _files_key = GCE.asymmetric_encrypt(new_receiver.crypto_pub_key, _files_key)
    else:
        _tip_key = _files_key = b''

    new_rtip = db_create_receivertip(session, new_receiver, itip, _tip_key, _files_key)
    new_rtip.new = False

    rfiles = session.query(models.ReceiverFile) \
                    .filter(models.ReceiverFile.receivertip_id == rtip.id)

    for rfile in rfiles:
        rf = models.ReceiverFile()
        rf.internalfile_id = rfile.internalfile_id
        rf.receivertip_id = new_rtip.id
        rf.filename = rfile.filename
        rf.new = False
        session.add(rf)

    db_tip_grant_notification(session, new_receiver)

    db_log(session, tid=tid, type='grant_access', user_id=user_id, object_id=itip.id)


def db_revoke_tip_access(session, tid, user_id, rtip_id, receiver_id):
    """
    Transaction for revoking a user access to a report

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip_id  of the submission object of the operation
    :param receiver_id: A user ID of the the user to which revoke access to the report
    """
    receiver, itip = session.query(models.User, models.InternalTip) \
                            .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                    models.ReceiverTip.id == rtip_id,
                                    models.User.id == models.ReceiverTip.receiver_id).one()

    if user_id == receiver_id or not receiver.can_grant_access_to_reports:
        raise errors.ForbiddenOperation

    rtip = session.query(models.ReceiverTip) \
                  .filter(models.ReceiverTip.internaltip_id == itip.id,
                          models.ReceiverTip.receiver_id == receiver_id).one_or_none()

    if rtip is None:
        return

    session.delete(rtip)

    db_log(session, tid=tid, type='revoke_access', user_id=user_id, object_id=itip.id)



def db_update_submission_status(session, tid, user_id, itip, status_id, substatus_id):
    """
    Transaction for registering a change of status of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user changing the state
    :param itip:  The ID of the submission
    :param status_id:  The new status ID
    :param substatus_id: A new substatus ID
    """
    if status_id == 'new':
        return

    itip.status = status_id
    itip.substatus = substatus_id or None

    log_data = {
      'status': itip.status,
      'substatus': itip.substatus
    }

    db_log(session, tid=tid, type='update_report_status', user_id=user_id, object_id=itip.id, data=log_data)


@transact
def update_tip_submission_status(session, tid, user_id, rtip_id, status_id, substatus_id):
    """
    Transaction for registering a change of status of a submission

    :param session: An ORM session
    :param tid: The tenant ID
    :param user_id: A user ID of the user changing the state
    :param rtip_id: The ID of the rtip accessed by the user
    :param status_id:  The new status ID
    :param substatus_id: A new substatus ID
    """
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    if itip.status != status_id or itip.substatus != substatus_id:
        itip.update_date = rtip.last_access = datetime_now()

    db_update_submission_status(session, tid, user_id, itip, status_id, substatus_id)


def db_access_rtip(session, tid, user_id, rtip_id):
    """
    Transaction retrieving an rtip and performing basic access checks

    :param session: An ORM session
    :param tid: A tenant ID of the user
    :param user_id: A user ID
    :param rtip_id: the requested rtip ID
    :return: A model requested
    """
    return db_get(session,
                  (models.User, models.ReceiverTip, models.InternalTip),
                  (models.User.id == user_id,
                   models.ReceiverTip.id == rtip_id,
                   models.ReceiverTip.receiver_id == models.User.id,
                   models.ReceiverTip.internaltip_id == models.InternalTip.id,
                   models.InternalTip.tid == tid))


def db_access_wbfile(session, tid, user_id, wbfile_id):
    """
    Transaction retrieving an wbfile and performing basic access checks

    :param session: An ORM session
    :param tid: A tenant ID of the user
    :param user_id: A user ID
    :param wbfile_id: the requested wbfile ID
    :return: A model requested
    """
    itips_ids = [x[0] for x in session.query(models.InternalTip.id)
                                      .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                              models.ReceiverTip.receiver_id == user_id,
                                              models.InternalTip.tid == tid)]

    return db_get(session,
                  models.WhistleblowerFile,
                  (models.WhistleblowerFile.id == wbfile_id,
                   models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                   models.ReceiverTip.internaltip_id.in_(itips_ids),
                   models.InternalTip.tid == tid))


@transact
def register_wbfile_on_db(session, tid, rtip_id, uploaded_file):
    """
    Register a file on the database

    :param session: An ORM session
    :param tid: A tenant id
    :param rtip_id: A id of the rtip on which attaching the file
    :param uploaded_file: A file to be attached
    :return: A descriptor of the file
    """
    rtip, itip = session.query(models.ReceiverTip, models.InternalTip) \
                        .filter(models.ReceiverTip.id == rtip_id,
                                models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                models.InternalTip.status != 'closed',
                                models.InternalTip.tid == tid).one()

    itip.update_date = rtip.last_access = datetime_now()

    if itip.crypto_tip_pub_key:
        for k in ['name', 'description', 'type', 'size']:
            if k == 'size':
                uploaded_file[k] = str(uploaded_file[k])
            uploaded_file[k] = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, uploaded_file[k]))

    new_file = models.WhistleblowerFile()

    new_file.name = uploaded_file['name']
    new_file.description = uploaded_file['description']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.receivertip_id = rtip_id
    new_file.filename = uploaded_file['filename']

    session.add(new_file)

    return serializers.serialize_wbfile(session, new_file)


def db_get_rtip(session, tid, user_id, rtip_id, language):
    """
    Transaction retrieving an rtip

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A user ID of the user opening the submission
    :param rtip_id: A rtip ID to accessed
    :param language: A language to be used for the serialization
    :return:  The serialized descriptor of the rtip
    """
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    if itip.status == 'new':
        db_update_submission_status(session, tid, user_id, itip, 'opened', None)

    rtip.last_access = datetime_now()
    if rtip.access_date == datetime_null():
        rtip.access_date = rtip.last_access

    db_log(session, tid=tid, type='access_report', user_id=user_id, object_id=itip.id)

    return serializers.serialize_rtip(session, itip, rtip, language), base64.b64decode(rtip.crypto_tip_prv_key)


@transact
def get_rtip(session, tid, user_id, rtip_id, language):
    """
    Transaction retrieving an rtip

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A user ID of the user opening the submission
    :param rtip_id: A rtip ID to accessed
    :param language: A language to be used for the serialization
    :return:  The serialized descriptor of the rtip
    """
    return db_get_rtip(session, tid, user_id, rtip_id, language)


def db_delete_itip(session, itip_id):
    """
    Transaction for deleting a submission

    :param session: An ORM session
    :param itip_id: A submission ID
    """
    db_del(session, models.InternalTip, models.InternalTip.id == itip_id)


def db_postpone_expiration(session, itip, expiration_date):
    """
    Transaction for postponing the expiration of a submission

    :param session: An ORM session
    :param itip: A submission model to be postponed
    :param expiration_date: The date timestamp to be set in milliseconds
    """
    expiration_date = expiration_date / 1000
    expiration_date = min(expiration_date, 32503680000)
    expiration_date = datetime.utcfromtimestamp(expiration_date)

    context = session.query(models.Context).filter(models.Context.id == itip.context_id).one()

    if context.tip_timetolive > 0:
        max_expiration_date = get_expiration(max(365, context.tip_timetolive * 2))
    else:
        max_expiration_date = datetime_never()

    if expiration_date > max_expiration_date:
        expiration_date = max_expiration_date

    if expiration_date > itip.expiration_date:
        itip.expiration_date = expiration_date

def db_set_reminder(session, itip, reminder_date):
    """
    Transaction for setting a reminder for a report

    :param session: An ORM session
    :param itip: A submission model to be postponed
    :param reminder_date: The date timestamp to be set in milliseconds
    """
    reminder_date = reminder_date / 1000
    reminder_date = min(reminder_date, 32503680000)
    reminder_date = datetime.utcfromtimestamp(reminder_date)

    itip.reminder_date = reminder_date

@transact
def delete_rtip(session, tid, user_id, rtip_id):
    """
    Transaction for deleting a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    """
    user, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    if not user.can_delete_submission:
        raise errors.ForbiddenOperation

    db_delete_itip(session, itip.id)

    db_log(session, tid=tid, type='delete_report', user_id=user_id, object_id=itip.id)


@transact
def postpone_expiration(session, tid, user_id, rtip_id, expiration_date):
    """
    Transaction for postponing the expiration of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    :param expiration_date: A new expiration date
    """
    user, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    if not user.can_postpone_expiration:
        raise errors.ForbiddenOperation

    db_postpone_expiration(session, itip, expiration_date)


@transact
def set_reminder(session, tid, user_id, rtip_id, reminder_date):
    """
    Transaction for postponing the expiration of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    :param reminder_date: A new reminder expiration date
    """
    user, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    db_set_reminder(session, itip, reminder_date)


@transact
def set_internaltip_variable(session, tid, user_id, rtip_id, key, value):
    """
    Transaction for setting properties of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    :param key: A key of the property to be set
    :param value: A value to be assigned to the property
    """
    _, _, itip = db_access_rtip(session, tid, user_id, rtip_id)
    setattr(itip, key, value)


@transact
def set_receivertip_variable(session, tid, user_id, rtip_id, key, value):
    """
    Transaction for setting properties of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    :param key: A key of the property to be set
    :param value: A value to be assigned to the property
    """
    _, rtip, _ = db_access_rtip(session, tid, user_id, rtip_id)
    setattr(rtip, key, value)


def db_create_identityaccessrequest_notifications(session, itip, rtip, iar):
    """
    Transaction for the creation of notifications related to identity access requests
    :param session: An ORM session
    :param itip: A itip ID of the tip involved in the request
    :param rtip: A rtip ID of the rtip involved in the request
    :param iar: A identity access request model
    """
    for user in session.query(models.User).filter(models.User.role == 'custodian',
                                                  models.User.tid == itip.tid,
                                                  models.User.notification.is_(True)):
        context = session.query(models.Context).filter(models.Context.id == itip.context_id).one()

        data = {
            'type': 'identity_access_request'
        }

        data['user'] = user_serialize_user(session, user, user.language)
        data['tip'] = serializers.serialize_rtip(session, itip, rtip, user.language)
        data['context'] = admin_serialize_context(session, context, user.language)
        data['iar'] = serializers.serialize_identityaccessrequest(session, iar)
        data['node'] = db_admin_serialize_node(session, itip.tid, user.language)

        if data['node']['mode'] == 'default':
            data['notification'] = db_get_notification(session, itip.tid, user.language)
        else:
            data['notification'] = db_get_notification(session, 1, user.language)

        subject, body = Templating().get_mail_subject_and_body(data)

        session.add(models.Mail({
            'address': data['user']['mail_address'],
            'subject': subject,
            'body': body,
            'tid': itip.tid
        }))


@transact
def create_identityaccessrequest(session, tid, user_id, rtip_id, request):
    """
    Transaction for the creation of notifications related to identity access requests
    :param session: An ORM session
    :param tid: A tenant ID of the user issuing the request
    :param user_id: A user ID of the user issuing the request
    :param rtip_id: A rtip_id ID of the rtip involved in the request
    :param request: The request data
    """
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    custodian = session.query(models.User).filter(models.User.tid == tid, models.User.role == 'custodian').count() > 0

    iar = models.IdentityAccessRequest()
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id

    if not custodian:
        iar.reply_date = datetime_now()
        iar.reply_user_id = user_id
        iar.reply = 'authorized'

    session.add(iar)
    session.flush()

    db_create_identityaccessrequest_notifications(session, itip, rtip, iar)

    return serializers.serialize_identityaccessrequest(session, iar)


@transact
def create_comment(session, tid, user_id, rtip_id, content):
    """
    Transaction for registering a new comment
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user id of the user creating the comment
    :param rtip_id: The rtip associated to the comment to be created
    :param content: The content of the comment
    :return: A serialized descriptor of the comment
    """
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    _content = content
    if itip.crypto_tip_pub_key:
        _content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()

    comment = models.Comment()
    comment.internaltip_id = itip.id
    comment.type = 'receiver'
    comment.author_id = rtip.receiver_id
    comment.content = _content
    session.add(comment)
    session.flush()

    ret = serializers.serialize_comment(session, comment)
    ret['content'] = content
    return ret



@transact
def create_message(session, tid, user_id, rtip_id, content):
    """
    Transaction for registering a new message
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user id of the user creating the message
    :param rtip_id: The rtip associated to the message to be created
    :param content: The content of the message
    :return: A serialized descriptor of the message
    """
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    _content = content
    if itip.crypto_tip_pub_key:
        _content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content)).decode()

    msg = models.Message()
    msg.receivertip_id = rtip.id
    msg.type = 'receiver'
    msg.content = _content
    session.add(msg)
    session.flush()

    ret = serializers.serialize_message(session, msg)
    ret['content'] = content
    return ret


@transact
def delete_wbfile(session, tid, user_id, file_id):
    """
    Transation for deleting a wbfile
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param file_id: The file ID of the wbfile to be deleted
    """
    wbfile = db_access_wbfile(session, tid, user_id, file_id)
    session.delete(wbfile)


class RTipInstance(OperationHandler):
    """
    This interface exposes the Receiver's Tip
    """
    check_roles = 'receiver'

    @inlineCallbacks
    def get(self, tip_id):
        tip, crypto_tip_prv_key = yield get_rtip(self.request.tid, self.session.user_id, tip_id, self.request.language)

        if State.tenants[self.request.tid].cache.encryption and crypto_tip_prv_key:
            tip = yield deferToThread(decrypt_tip, self.session.cc, crypto_tip_prv_key, tip)

        returnValue(tip)

    def operation_descriptors(self):
        return {
          'grant': RTipInstance.grant_tip_access,
          'revoke': RTipInstance.revoke_tip_access,
          'postpone': RTipInstance.postpone_expiration,
          'set_reminder': RTipInstance.set_reminder,
          'set': RTipInstance.set_tip_val,
          'update_status': RTipInstance.update_submission_status
        }

    def set_tip_val(self, req_args, rtip_id, *args, **kwargs):
        value = req_args['value']
        key = req_args['key']

        if key == 'enable_notifications':
            return set_receivertip_variable(self.request.tid, self.session.user_id, rtip_id, key, value)

        return set_internaltip_variable(self.request.tid, self.session.user_id, rtip_id, key, value)

    def grant_tip_access(self, req_args, rtip_id, *args, **kwargs):
        return tw(db_grant_tip_access, self.request.tid, self.session.user_id, self.session.cc, rtip_id, req_args['receiver'])

    def revoke_tip_access(self, req_args, rtip_id, *args, **kwargs):
        return tw(db_revoke_tip_access, self.request.tid, self.session.user_id, rtip_id, req_args['receiver'])

    def postpone_expiration(self, req_args, rtip_id, *args, **kwargs):
        return postpone_expiration(self.request.tid, self.session.user_id, rtip_id, req_args['value'])

    def set_reminder(self, req_args, rtip_id, *args, **kwargs):
        return set_reminder(self.request.tid, self.session.user_id, rtip_id, req_args['value'])

    def update_submission_status(self, req_args, rtip_id, *args, **kwargs):
        return update_tip_submission_status(self.request.tid, self.session.user_id, rtip_id,
                                            req_args['status'], req_args['substatus'])

    def delete(self, rtip_id):
        """
        Remove the Internaltip and all the associated data
        """
        return delete_rtip(self.request.tid, self.session.user_id, rtip_id)


class RTipCommentCollection(BaseHandler):
    """
    Interface use to write rtip comments
    """
    check_roles = 'receiver'

    def post(self, rtip_id):
        request = self.validate_request(self.request.content.read(), requests.CommentDesc)

        return create_comment(self.request.tid, self.session.user_id, rtip_id, request['content'])


class ReceiverMsgCollection(BaseHandler):
    """
    Interface use to write rtip messages
    """
    check_roles = 'receiver'

    def post(self, rtip_id):
        request = self.validate_request(self.request.content.read(), requests.CommentDesc)

        return create_message(self.request.tid, self.session.user_id, rtip_id, request['content'])


class ReceiverFileDownload(BaseHandler):
    """
    This handler exposes rfiles for download.
    """
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @transact
    def download_rfile(self, session, tid, user_id, file_id):
        rfile, ifile, rtip, pgp_key = db_get(session,
                                             (models.ReceiverFile,
                                              models.InternalFile,
                                              models.ReceiverTip,
                                              models.User.pgp_key_public),
                                             (models.ReceiverTip.receiver_id == models.User.id,
                                              models.ReceiverTip.id == models.ReceiverFile.receivertip_id,
                                              models.InternalFile.id == models.ReceiverFile.internalfile_id,
                                              models.ReceiverFile.id == file_id,
                                              models.User.id == user_id))

        if rfile.access_date == datetime_null():
            rfile.access_date = datetime_now()

        log.debug("Download of file %s by receiver %s" %
                  (rfile.internalfile_id, rtip.receiver_id))

        return ifile.name, rfile.filename, base64.b64decode(rtip.crypto_tip_prv_key), base64.b64decode(rtip.crypto_files_prv_key), pgp_key

    @inlineCallbacks
    def get(self, rfile_id):
        name, filename, tip_prv_key, files_prv_key, pgp_key = yield self.download_rfile(self.request.tid, self.session.user_id, rfile_id)

        filelocation = os.path.join(self.state.settings.attachments_path, filename)
        directory_traversal_check(self.state.settings.attachments_path, filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.session.cc, tip_prv_key)
            files_prv_key = GCE.asymmetric_decrypt(self.session.cc, files_prv_key)
            name = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(name.encode())).decode()

        if filelocation.endswith('.encrypted'):
            filelocation = GCE.streaming_encryption_open('DECRYPT', files_prv_key, filelocation)
        elif 'pgp' in filelocation:
            pgp_key = ''
            name += ".pgp"

        yield self.write_file_as_download(name, filelocation, pgp_key)


class WhistleblowerFileHandler(BaseHandler):
    """
    Receiver interface to upload a file intended for the whistleblower
    """
    check_roles = 'receiver'
    upload_handler = True

    @inlineCallbacks
    def post(self, rtip_id):
        yield register_wbfile_on_db(self.request.tid, rtip_id, self.uploaded_file)

        log.debug("Recorded new WhistleblowerFile %s",
                  self.uploaded_file['name'])


class RTipWBFileHandler(BaseHandler):
    """
    This handler lets the recipient download and delete wbfiles, which are files
    intended for delivery to the whistleblower.
    """
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @transact
    def download_wbfile(self, session, tid, file_id):
        wbfile, wbtip, pgp_key = db_get(session,
                                        (models.WhistleblowerFile,
                                         models.InternalTip,
                                         models.User.pgp_key_public),
                                        (models.User.id == models.ReceiverTip.receiver_id,
                                         models.WhistleblowerFile.id == file_id,
                                         models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                                         models.ReceiverTip.internaltip_id == models.InternalTip.id))

        rtip = session.query(models.ReceiverTip) \
                      .filter(models.ReceiverTip.receiver_id == self.session.user_id,
                              models.ReceiverTip.internaltip_id == wbtip.id).one_or_none()
        if not rtip:
            raise errors.ResourceNotFound

        return wbfile.name, wbfile.filename, base64.b64decode(rtip.crypto_tip_prv_key), pgp_key

    @inlineCallbacks
    def get(self, wbfile_id):
        name, filename, tip_prv_key, pgp_key = yield self.download_wbfile(self.request.tid, wbfile_id)

        filelocation = os.path.join(self.state.settings.attachments_path, filename)
        directory_traversal_check(self.state.settings.attachments_path, filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.session.cc, tip_prv_key)
            name = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(name.encode())).decode()
            filelocation = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, filelocation)

        yield self.write_file_as_download(name, filelocation, pgp_key)

    def delete(self, file_id):
        """
        This interface allow the recipient to set the description of a WhistleblowerFile
        """
        return delete_wbfile(self.request.tid, self.session.user_id, file_id)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    Handler responsible of the creation of identity access requests
    """
    check_roles = 'receiver'

    def post(self, rtip_id):
        request = self.validate_request(self.request.content.read(), requests.ReceiverIdentityAccessRequestDesc)

        return create_identityaccessrequest(self.request.tid,
                                            self.session.user_id,
                                            rtip_id,
                                            request)
