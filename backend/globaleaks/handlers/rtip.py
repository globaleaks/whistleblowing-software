# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for receivers (rtip)
import base64
import os

from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.custodian import serialize_identityaccessrequest
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.submission import serialize_usertip, decrypt_tip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.models import serializers
from globaleaks.orm import db_get, db_del, transact
from globaleaks.rest import errors, requests
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.crypto import GCE
from globaleaks.utils.fs import directory_traversal_check
from globaleaks.utils.log import log
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import get_expiration, datetime_now, datetime_never


def db_update_submission_status(session, user_id, itip, status_id, substatus_id):
    """
    Transaction for registering a change of status of a submission

    :param session: An ORM session
    :param user_id: A user ID of the user changing the state
    :param itip:  The ID of the submission
    :param status_id:  The new status ID
    :param substatus_id: A new substatus ID
    """
    if status_id == 'new':
        return

    itip.status = status_id
    itip.substatus = substatus_id or None
    submission_status_change = models.SubmissionStatusChange()
    submission_status_change.internaltip_id = itip.id
    submission_status_change.status = status_id
    submission_status_change.substatus = substatus_id or None
    submission_status_change.changed_by = user_id

    session.add(submission_status_change)


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
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    db_update_submission_status(session, user_id, itip, status_id, substatus_id)


def receiver_serialize_rfile(session, rfile):
    """
    Transaction returning a serialized descriptor of an rfile

    :param session: An ORM session
    :param rfile: A model to be serialized
    :return: A serialized description of the model specified
    """
    ifile = session.query(models.InternalFile) \
                   .filter(models.InternalFile.id == rfile.internalfile_id).one_or_none()

    return {
        'id': rfile.id,
        'internalfile_id': ifile.id,
        'status': rfile.status,
        'href': "/rtip/" + rfile.receivertip_id + "/download/" + rfile.id,
        'name': ifile.name,
        'filename': rfile.filename,
        'type': ifile.content_type,
        'creation_date': ifile.creation_date,
        'size': ifile.size,
        'downloads': rfile.downloads,
        'path': os.path.join(Settings.attachments_path, rfile.filename)
    }


def receiver_serialize_wbfile(session, wbfile):
    """
    Transaction returning a serialized descriptor of an wbfile

    :param session: An ORM session
    :param wbfile: A model to be serialized
    :return: A serialized description of the model specified
    """
    rtip = db_get(session,
                  models.ReceiverTip,
                  models.ReceiverTip.id == wbfile.receivertip_id)

    return {
        'id': wbfile.id,
        'creation_date': wbfile.creation_date,
        'name': wbfile.name,
        'filename': wbfile.filename,
        'description': wbfile.description,
        'size': wbfile.size,
        'type': wbfile.content_type,
        'downloads': wbfile.downloads,
        'author': rtip.receiver_id,
        'path': os.path.join(Settings.attachments_path, wbfile.filename)
    }


def serialize_comment(session, comment):
    """
    Transaction returning a serialized descriptor of a comment

    :param session: An ORM session
    :param comment: A model to be serialized
    :return: A serialized description of the model specified
    """
    return {
        'id': comment.id,
        'type': comment.type,
        'creation_date': comment.creation_date,
        'content': comment.content,
        'author': comment.author_id
    }


def serialize_message(session, message):
    """
    Transaction returning a serialized descriptor of a message

    :param session: An ORM session
    :param message: A model to be serialized
    :return: A serialized description of the model specified
    """
    receiver_involved_id = session.query(models.ReceiverTip.receiver_id) \
                                  .filter(models.ReceiverTip.id == models.Message.receivertip_id,
                                          models.Message.id == message.id).one()

    return {
        'id': message.id,
        'type': message.type,
        'creation_date': message.creation_date,
        'content': message.content,
        'receiver_involved_id': receiver_involved_id
    }


def serialize_rtip(session, rtip, itip, language):
    """
    Transaction returning a serialized descriptor of a tip

    :param session: An ORM session
    :param rtip: A model to be serialized
    :param itip: A itip object referenced by the model to be serialized
    :param language: A language of the serialization
    :return: A serialized description of the model specified
    """
    user_id = rtip.receiver_id

    ret = serialize_usertip(session, rtip, itip, language)

    if 'whistleblower_identity' in ret['data']:
        ret['data']['whistleblower_identity_provided'] = True

        if not rtip.can_access_whistleblower_identity:
            del ret['data']['whistleblower_identity']

    ret['id'] = rtip.id
    ret['receiver_id'] = user_id

    if State.tenant_cache[itip.tid].enable_private_annotations:
        ret['important'] = rtip.important
        ret['label'] = rtip.label
    else:
        ret['important'] = itip.important
        ret['label'] = itip.label

    ret['comments'] = db_get_itip_comment_list(session, itip.id)
    ret['messages'] = db_get_itip_message_list(session, rtip.id)
    ret['rfiles'] = db_receiver_get_rfile_list(session, rtip.id)
    ret['wbfiles'] = db_receiver_get_wbfile_list(session, itip.id)
    ret['iars'] = db_get_rtip_identityaccessrequest_list(session, rtip.id)
    ret['enable_notifications'] = bool(rtip.enable_notifications)

    return ret


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
                  (models.ReceiverTip, models.InternalTip),
                  (models.ReceiverTip.id == rtip_id,
                   models.ReceiverTip.receiver_id == user_id,
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
    itips_ids = [x[0] for x in session.query(models.InternalTip.id) \
                                      .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                              models.ReceiverTip.receiver_id == user_id,
                                              models.InternalTip.tid == tid)]

    return db_get(session,
                  models.WhistleblowerFile,
                  (models.WhistleblowerFile.id == wbfile_id,
                   models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                   models.ReceiverTip.internaltip_id.in_(itips_ids),
                   models.InternalTip.tid == tid))


def db_receiver_get_rfile_list(session, rtip_id):
    """
    Transaction retrieving the list of rfiles attached to an rtip

    :param session: An ORM session
    :param rtip_id: A rtip ID
    :return: A list of serializations of the retrieved models
    """
    rfiles = session.query(models.ReceiverFile) \
                    .filter(models.ReceiverFile.receivertip_id == rtip_id)

    return [receiver_serialize_rfile(session, rfile) for rfile in rfiles]


@transact
def receiver_get_rfile_list(session, rtip_id):
    """
    Transaction retrieving the list of rfiles attached to an rtip

    :param session: An ORM session
    :param rtip_id: A rtip ID
    :return: A list of serializations of the retrieved models
    """
    return db_receiver_get_rfile_list(session, rtip_id)


def db_receiver_get_wbfile_list(session, itip_id):
    """
    Transaction retrieving the list of rfiles attached to an itip

    :param session: An ORM session
    :param itip_id: A itip ID
    :return: A list of serializations of the retrieved models
    """
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


def db_set_itip_open_if_new(session, tid, user_id, itip):
    """
    Transaction setting a submission status to open if the current status is new

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A user ID of the user opening the submission
    :param itip: A submission
    """
    new_status_id = session.query(models.SubmissionStatus.id) \
                           .filter(models.SubmissionStatus.id == 'new',
                                   models.SubmissionStatus.tid == tid).one()[0]

    if new_status_id == itip.status:
        open_status_id = session.query(models.SubmissionStatus.id) \
                                .filter(models.SubmissionStatus.id == 'opened',
                                        models.SubmissionStatus.tid == tid).one()[0]

        db_update_submission_status(session, user_id, itip, open_status_id, '')


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
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    db_set_itip_open_if_new(session, tid, user_id, itip)

    rtip.access_counter += 1
    rtip.last_access = datetime_now()

    return serialize_rtip(session, rtip, itip, language), base64.b64decode(rtip.crypto_tip_prv_key)


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


def db_postpone_expiration(session, itip):
    """
    Transaction for postponing the expiration of a submission

    :param session: An ORM session
    :param itip: A submission model to be postponed
    """
    context = session.query(models.Context).filter(models.Context.id == itip.context_id).one()

    if context.tip_timetolive > 0:
        itip.expiration_date = get_expiration(context.tip_timetolive)
    else:
        itip.expiration_date = datetime_never()


@transact
def delete_rtip(session, tid, user_id, rtip_id):
    """
    Transaction for deleting a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    """
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    receiver = db_get(session,
                      models.User,
                      models.User.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_delete_submission or
            receiver.can_delete_submission):
        raise errors.ForbiddenOperation

    State.log(tid=tid, type='delete_report', user_id=user_id, object_id=itip.id)

    db_delete_itip(session, itip.id)


@transact
def postpone_expiration(session, tid, user_id, rtip_id):
    """
    Transaction for postponing the expiration of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    """
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    receiver = db_get(session,
                      models.User,
                      models.User.id == rtip.receiver_id)

    if not (State.tenant_cache[tid].can_postpone_expiration or
            receiver.can_postpone_expiration):
        raise errors.ForbiddenOperation

    db_postpone_expiration(session, itip)


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
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)
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
    rtip, _ = db_access_rtip(session, tid, user_id, rtip_id)
    setattr(rtip, key, value)


@transact
def update_label(session, tid, user_id, rtip_id, value):
    """
    Transaction for setting the label of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    :param value: A value to be assigned to the label property
    """
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    if State.tenant_cache[tid].enable_private_annotations:
        setattr(rtip, 'label', value)
    else:
        setattr(itip, 'label', value)


@transact
def update_important(session, tid, user_id, rtip_id, value):
    """
    Transaction for setting the important flag of a submission

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip ID of the submission object of the operation
    :param value: A value to be assigned to important flag
    """
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    if State.tenant_cache[tid].enable_private_annotations:
        setattr(rtip, 'important', value)
    else:
        setattr(itip, 'important', value)


def db_get_itip_comment_list(session, itip_id):
    """
    Transaction for retrieving the list of comments associated to a submission
    :param session: An ORM session
    :param itip_id: A submission object of the request
    :return: A serialized descriptor of the comments
    """
    return [serialize_comment(session, comment) for comment in session.query(models.Comment).filter(models.Comment.internaltip_id == itip_id)]


def db_create_identityaccessrequest_notifications(session, itip, rtip, iar):
    """
    Transaction for the creation of notifications related to identity access requests
    :param session: An ORM session
    :param tid: A tenant ID on which the request is issued
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
        data['tip'] = serialize_rtip(session, rtip, itip, user.language)
        data['context'] = admin_serialize_context(session, context, user.language)
        data['iar'] = serialize_identityaccessrequest(session, iar)
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
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    iar = models.IdentityAccessRequest()
    iar.request_motivation = request['request_motivation']
    iar.receivertip_id = rtip.id
    session.add(iar)
    session.flush()

    db_create_identityaccessrequest_notifications(session, itip, rtip, iar)

    return serialize_identityaccessrequest(session, iar)


def db_get_rtip_identityaccessrequest_list(session, rtip_id):
    """
    Transaction for retrieving identity associated to an rtip
    :param session: An ORM session
    :param rtip_id: An rtip ID
    :return: The list of descriptors of the identity access requests associated to the specified rtip
    """
    return [serialize_identityaccessrequest(session, iar) for iar in session.query(models.IdentityAccessRequest).filter(models.IdentityAccessRequest.receivertip_id == rtip_id)]


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
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

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

    ret = serialize_comment(session, comment)
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
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

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

    ret = serialize_message(session, msg)
    ret['content'] = content
    return ret


def db_get_itip_message_list(session, rtip_id):
    """
    Transact for retrieving the list of comments associated to a tip
    :param session: An ORM session
    :param rtip_id: An rtip ID
    :return: A serialized list of descriptors of messages associated to the specified rtip
    """
    return [serialize_message(session, message) for message in session.query(models.Message).filter(models.Message.receivertip_id == rtip_id)]


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

        if State.tenant_cache[self.request.tid].encryption and crypto_tip_prv_key:
            tip = yield deferToThread(decrypt_tip, self.session.cc, crypto_tip_prv_key, tip)

        self.state.log(tid=self.session.tid, type='access_report', user_id=self.session.user_id, object_id=tip['internaltip_id'])

        returnValue(tip)

    def operation_descriptors(self):
        return {
          'postpone_expiration': (RTipInstance.postpone_expiration, None),
          'set': (RTipInstance.set_tip_val,
                  {'key': '^(enable_two_way_comments|enable_two_way_messages|enable_attachments|enable_notifications)$',
                   'value': bool}),
          'update_label': (RTipInstance.update_label, {'value': str}),
          'update_important': (RTipInstance.update_important, {'value': bool}),
          'update_status': (RTipInstance.update_submission_status, {'status': str,
                                                                    'substatus': str})
        }

    def set_tip_val(self, req_args, tip_id, *args, **kwargs):
        value = req_args['value']
        key = req_args['key']

        if key == 'enable_notifications':
            return set_receivertip_variable(self.request.tid, self.session.user_id, tip_id, key, value)

        return set_internaltip_variable(self.request.tid, self.session.user_id, tip_id, key, value)

    def postpone_expiration(self, _, tip_id, *args, **kwargs):
        return postpone_expiration(self.request.tid, self.session.user_id, tip_id)

    def update_important(self, req_args, tip_id, *args, **kwargs):
        return update_important(self.request.tid, self.session.user_id, tip_id, req_args['value'])

    def update_label(self, req_args, tip_id, *args, **kwargs):
        return update_label(self.request.tid, self.session.user_id, tip_id, req_args['value'])

    def update_submission_status(self, req_args, tip_id, *args, **kwargs):
        return update_tip_submission_status(self.request.tid, self.session.user_id, tip_id,
                                            req_args['status'], req_args['substatus'])

    def delete(self, tip_id):
        """
        Remove the Internaltip and all the associated data
        """
        return delete_rtip(self.request.tid, self.session.user_id, tip_id)


class RTipCommentCollection(BaseHandler):
    """
    Interface use to write rtip comments
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_comment(self.request.tid, self.session.user_id, tip_id, request['content'])


class ReceiverMsgCollection(BaseHandler):
    """
    Interface use to write rtip messages
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.CommentDesc)

        return create_message(self.request.tid, self.session.user_id, tip_id, request['content'])


class WhistleblowerFileHandler(BaseHandler):
    """
    Receiver interface to upload a file intended for the whistleblower
    """
    check_roles = 'receiver'
    upload_handler = True

    @transact
    def can_perform_action(self, session, tid, tip_id, filename):
        rtip, _ = db_access_rtip(session, tid, self.session.user_id, tip_id)

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

        log.debug("Recorded new WhistleblowerFile %s",
                  self.uploaded_file['name'])


class WBFileHandler(BaseHandler):
    """
    This class is used in both RTip and WBTip to define a base for respective handlers
    """
    check_roles = 'receiver'
    require_token = [b'GET']
    handler_exec_time_threshold = 3600

    def user_can_access(self, session, tid, wbfile):
        raise NotImplementedError("This class defines the user_can_access interface.")

    def access_wbfile(self, session, wbfile):
        pass

    @transact
    def download_wbfile(self, session, tid, file_id):
        wbfile, wbtip, = db_get(session,
                                (models.WhistleblowerFile,
                                 models.WhistleblowerTip),
                                (models.WhistleblowerFile.id == file_id,
                                 models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                                 models.ReceiverTip.internaltip_id == models.WhistleblowerTip.id))

        rtip = session.query(models.ReceiverTip) \
                      .filter(models.ReceiverTip.receiver_id == self.session.user_id,
                              models.ReceiverTip.internaltip_id == wbtip.id).one_or_none()
        if not rtip:
            raise errors.ResourceNotFound()

        self.access_wbfile(session, wbfile)

        return serializers.serialize_wbfile(session, wbfile), base64.b64decode(rtip.crypto_tip_prv_key)

    @inlineCallbacks
    def get(self, wbfile_id):
        wbfile, tip_prv_key = yield self.download_wbfile(self.request.tid, wbfile_id)

        filelocation = os.path.join(Settings.attachments_path, wbfile['filename'])

        directory_traversal_check(Settings.attachments_path, filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.session.cc, tip_prv_key)
            wbfile['name'] = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(wbfile['name'].encode())).decode()
            filelocation = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, filelocation)

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

        return self.session.user_id in users_ids

    def delete(self, file_id):
        """
        This interface allow the recipient to set the description of a WhistleblowerFile
        """
        return delete_wbfile(self.request.tid, self.session.user_id, file_id)


class ReceiverFileDownload(BaseHandler):
    """
    This handler exposes rfiles for download.
    """
    check_roles = 'receiver'
    require_token = [b'GET']
    handler_exec_time_threshold = 3600

    @transact
    def download_rfile(self, session, tid, user_id, file_id):
        rfile, rtip = db_get(session,
                             (models.ReceiverFile, models.ReceiverTip),
                             (models.ReceiverFile.id == file_id,
                              models.ReceiverFile.receivertip_id == models.ReceiverTip.id,
                              models.ReceiverTip.receiver_id == user_id,
                              models.ReceiverTip.internaltip_id == models.InternalTip.id,
                              models.InternalTip.tid == tid))

        log.debug("Download of file %s by receiver %s (%d)" %
                  (rfile.internalfile_id, rtip.receiver_id, rfile.downloads))

        rfile.last_access = datetime_now()
        rfile.downloads += 1

        return serializers.serialize_rfile(session, rfile), base64.b64decode(rtip.crypto_tip_prv_key)

    @inlineCallbacks
    def get(self, rfile_id):
        rfile, tip_prv_key = yield self.download_rfile(self.request.tid, self.session.user_id, rfile_id)

        filelocation = os.path.join(Settings.attachments_path, rfile['filename'])
        directory_traversal_check(Settings.attachments_path, filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.session.cc, tip_prv_key)
            rfile['name'] = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(rfile['name'].encode())).decode()

        if rfile['status'] == 'encrypted':
            rfile['name'] += ".pgp"

        if tip_prv_key and rfile['status'] != 'encrypted':
            filelocation = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, filelocation)

        yield self.write_file_as_download(rfile['name'], filelocation)



class IdentityAccessRequestsCollection(BaseHandler):
    """
    Handler responsible of the creation of identity access requests
    """
    check_roles = 'receiver'

    def post(self, tip_id):
        request = self.validate_message(self.request.content.read(), requests.ReceiverIdentityAccessRequestDesc)

        return create_identityaccessrequest(self.request.tid,
                                            self.session.user_id,
                                            tip_id,
                                            request)
