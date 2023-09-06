# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for receivers (rtip)
import base64
import json
import os
import time

from datetime import datetime, timedelta

from twisted.internet.threads import deferToThread
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.whistleblower.submission import db_create_receivertip, decrypt_tip
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
from globaleaks.utils.json import JSONEncoder


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


def db_grant_tip_access(session, tid, user_id, user_cc, itip, rtip, receiver_id):
    """
    Transaction for granting a user access to a report

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param user_cc: A user crypto key
    :param rtip_id: A rtip_id of the rtip on which perform the operation
    :param receiver_id: A user ID of the the user to which grant access to the report
    """
    existing = session.query(models.ReceiverTip).filter(models.ReceiverTip.receiver_id == receiver_id,
                                                        models.ReceiverTip.internaltip_id == itip.id).one_or_none()

    if existing:
        return False

    new_receiver = db_get(session,
                          models.User,
                          models.User.id == receiver_id)

    if itip.crypto_tip_pub_key and not new_receiver.crypto_pub_key:
        # Access to encrypted submissions could be granted only if the recipient has performed first login
        return
    _tip_key = b''
    if itip.crypto_tip_pub_key:
        _tip_key = GCE.asymmetric_decrypt(user_cc, base64.b64decode(rtip.crypto_tip_prv_key))
        _tip_key = GCE.asymmetric_encrypt(new_receiver.crypto_pub_key, _tip_key)

    new_rtip = db_create_receivertip(session, new_receiver, itip, _tip_key)
    new_rtip.new = False
    if itip.deprecated_crypto_files_pub_key:
        _files_key = GCE.asymmetric_decrypt(user_cc, base64.b64decode(rtip.deprecated_crypto_files_prv_key))
        new_rtip.deprecated_crypto_files_prv_key = base64.b64encode(GCE.asymmetric_encrypt(new_receiver.crypto_pub_key, _files_key))

    wbfiles = session.query(models.WhistleblowerFile) \
                    .filter(models.WhistleblowerFile.receivertip_id == rtip.id)

    for wbfile in wbfiles:
        rf = models.WhistleblowerFile()
        rf.internalfile_id = wbfile.internalfile_id
        rf.receivertip_id = new_rtip.id
        rf.new = False
        session.add(rf)

    db_tip_grant_notification(session, new_receiver)

    return True


def db_revoke_tip_access(session, tid, user_id, itip, receiver_id):
    """
    Transaction for revoking a user access to a report

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: A rtip_id  of the submission object of the operation
    :param receiver_id: A user ID of the the user to which revoke access to the report
    """
    rtip = session.query(models.ReceiverTip) \
                  .filter(models.ReceiverTip.internaltip_id == itip.id,
                          models.ReceiverTip.receiver_id == receiver_id).one_or_none()
    if rtip is None:
        return False

    session.delete(rtip)

    return True


@transact
def grant_tip_access(session, tid, user_id, user_cc, rtip_id, receiver_id):
    user, itip, rtip = session.query(models.User, models.InternalTip, models.ReceiverTip) \
                                  .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                          models.ReceiverTip.id == rtip_id,
                                          models.User.id == models.ReceiverTip.receiver_id).one()
    if user_id == receiver_id or not user.can_grant_access_to_reports:
        raise errors.ForbiddenOperation

    if db_grant_tip_access(session, tid, user, user_cc, itip, rtip, receiver_id):
        db_log(session, tid=tid, type='grant_access', user_id=user_id, object_id=itip.id)


@transact
def revoke_tip_access(session, tid, user_id, rtip_id, receiver_id):
    user, itip, rtip = session.query(models.User, models.InternalTip, models.ReceiverTip) \
                                  .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                          models.ReceiverTip.id == rtip_id,
                                          models.User.id == models.ReceiverTip.receiver_id).one()
    if user_id == receiver_id or not user.can_grant_access_to_reports:
        raise errors.ForbiddenOperation

    if db_revoke_tip_access(session, tid, user, itip, receiver_id):
        db_log(session, tid=tid, type='revoke_access', user_id=user_id, object_id=itip.id)


@transact
def transfer_tip_access(session, tid, user_id, user_cc, rtip_id, receiver_id):
    log_data = {
      'recipient_id': receiver_id
    }

    user, itip, rtip = session.query(models.User, models.InternalTip, models.ReceiverTip) \
                                  .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                          models.ReceiverTip.id == rtip_id,
                                          models.User.id == models.ReceiverTip.receiver_id).one()
    if user_id == receiver_id or not user.can_transfer_access_to_reports:
        raise errors.ForbiddenOperation

    if not db_grant_tip_access(session, tid, user, user_cc, itip, rtip, receiver_id):
        raise errors.ForbiddenOperation

    if not db_revoke_tip_access(session, tid, user, itip, user_id):
        raise errors.ForbiddenOperation

    db_log(session, tid=tid, type='transfer_access', user_id=user_id, object_id=itip.id, data=log_data)


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


def db_update_redaction(session, tid, user_id, itip_id, object_id, redaction_data):
    """
    Update the redaction data of a tip

    :param session: An ORM session
    :param tid: The tenant ID
    :param user_id: The user ID of the user changing the state
    :param itip_id: The ID of the Tip instance to be updated
    :param object_id: The object_id
    :param redaction_data: The updated redaction data
    """
    redaction = session.query(models.Redaction).get(object_id)
    if not redaction:
        return

    redaction.reference_id = redaction_data['reference_id']
    redaction.temporary_redaction = redaction_data['temporary_redaction']
    redaction.permanent_redaction = redaction_data['permanent_redaction']
    redaction.update_date = datetime.now()

    log_data = {
        'reference_id': redaction_data['reference_id'],
        'creation_date': redaction.update_date,
        'temporary_redaction': redaction_data['temporary_redaction'],
        'permanent_redaction': redaction_data['permanent_redaction']
    }

    db_log(session, tid=tid, type='update_redaction', user_id=user_id, object_id=object_id, data=log_data)


def redact_content(content, temporary_ranges, permanent_ranges):
    """
    permanently redact the textual content

    :param content: textual content to be updated
    :param temporary_ranges: temporary masking ranges
    :param permanent_ranges: permanent masking ranges
    """

    for r in temporary_ranges:
        content = content[:r["start"]] + "*" * (r["end"] - r["start"] + 1) + content[r["start"]:]

    content = list(content)
    for r in permanent_ranges:
        start, end = r.get('start', 0), r.get('end', 0) + 1
        end = min(end, len(content))
        if start < end:
            content[start:end] = '*' * (end - start)

    return ''.join(content).replace('*', '') or ' '


def merge_dicts(temporary_ranges, permanent_ranges):
    """
    Merge ranges for permanent redaction

    :param temporary_ranges: set of temporary ranges
    :param permanent_ranges: set of permanent ranges
    """

    merged_list = temporary_ranges + permanent_ranges
    merged_list.sort(key=lambda x: x['start'])  # Sort by 'start' key
    i = 1

    while i < len(merged_list):
        if merged_list[i]['start'] <= merged_list[i - 1]['end']:
            merged_list[i - 1]['end'] = max(merged_list[i - 1]['end'], merged_list[i]['end'])
            del merged_list[i]
        else:
            i += 1

    return merged_list


def db_mask_data(session, redaction, temporary_ranges, permanent_ranges, redaction_data, content, tid, user_id, object_id):
    """
    Transaction for updating masked data

    :param session: An ORM Session
    :param redaction: model tracking content redaction
    :param temporary_ranges: new permanent ranges that to be marked
    :param permanent_ranges: existing temporary ranges that are marked
    :param content: textual content to be updated
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param id: The ID of the redaction to be deleted
    :param masked_marker: Object used to update redaction in database
    :param id: The ID of the redaction to be deleted
    """

    tempRedaction = temporary_ranges
    if permanent_ranges:
        permanentRedaction = permanent_ranges
        permanentRedaction = merge_dicts(tempRedaction, permanentRedaction)
    else:
        permanentRedaction = tempRedaction

    redaction.reference_id = redaction_data['reference_id']
    redaction.update_date = datetime.now()
    redaction.temporary_redaction = []
    redaction.permanent_redaction = permanentRedaction

    redaction_log_data = {
        'temporary_redaction': [],
    }

    db_log(session, tid=tid, type='update_redaction', user_id=user_id, object_id=object_id, data=redaction_log_data)


def db_mask_comments(session, tid, user_id, itip_id, content_id, redaction_data, tip_data, content_type, mask):
    masked_content = next((masked_content for masked_content in tip_data.get(content_type, []) if masked_content['id'] == redaction_data['reference_id']), None)

    if masked_content:
        redaction = session.query(models.Redaction).get(content_id)

    if redaction:
        content = redact_content(masked_content.get('content'), redaction.permanent_redaction, redaction.temporary_redaction)
        content = base64.b64encode(GCE.asymmetric_encrypt(itip_id.crypto_tip_pub_key, content)).decode()
        db_mask_data(session, redaction, redaction.temporary_redaction, redacton.permanent_redaction, redaction_data, content, tid, user_id, content_id)


def db_mask_answer(session, tid, user_id, itip_id, content_id, redaction_data, tip_data):
    redaction_data = next((masked_content for masked_content in tip_data['redaction'] if masked_content['reference_id'] == redaction_data['reference_id']), None)
    tip_data = tip_data['questionnaires'][0]

    for key, value in tip_data['answers'].items():
        # FIX: should be recursive
        if key == redaction_data['reference_id']:
            content_data = value[0]
            content = redact_content(content_data['value'], redaction_data['permanent_redaction'], redaction_data['temporary_redaction'])
            tip_data['answers'][key][0]['value'] = content
            redaction = session.query(models.Redaction).get(content_id)
            db_mask_data(session, redaction, redaction_data['temporary_redaction'], redaction_data['permanent_redaction'], redaction_data, content, tid, user_id, content_id)
            break

    _content = tip_data['answers']
    if itip_id.crypto_tip_pub_key:
        _content = base64.b64encode(GCE.asymmetric_encrypt(itip_id.crypto_tip_pub_key, json.dumps(_content, cls=JSONEncoder).encode())).decode()

    answers = session.query(models.InternalTipAnswers).filter_by(internaltip_id=redaction_data['internaltip_id']).first()
    if answers:
        answers.content = _content


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


def db_access_rfile(session, tid, user_id, rfile_id):
    """
    Transaction retrieving an rfile and performing basic access checks

    :param session: An ORM session
    :param tid: A tenant ID of the user
    :param user_id: A user ID
    :param rfile_id: the requested rfile ID
    :return: A model requested
    """
    itips_ids = [x[0] for x in session.query(models.InternalTip.id)
                                      .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                              models.ReceiverTip.receiver_id == user_id,
                                              models.InternalTip.tid == tid)]

    return db_get(session,
                  models.ReceiverFile,
                  (models.ReceiverFile.id == rfile_id,
                   models.ReceiverFile.internaltip_id.in_(itips_ids),
                   models.InternalTip.tid == tid))


@transact
def register_rfile_on_db(session, tid, user_id, rtip_id, uploaded_file):
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
                                models.ReceiverTip.receiver_id == user_id,
                                models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                models.InternalTip.status != 'closed',
                                models.InternalTip.tid == tid).one()

    itip.update_date = rtip.last_access = datetime_now()

    if itip.crypto_tip_pub_key:
        for k in ['name', 'description', 'type', 'size']:
            if k == 'size':
                uploaded_file[k] = str(uploaded_file[k])
            uploaded_file[k] = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, uploaded_file[k]))

    new_file = models.ReceiverFile()
    new_file.id = uploaded_file['filename']
    new_file.author_id = user_id
    new_file.name = uploaded_file['name']
    new_file.description = uploaded_file['description']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.internaltip_id = itip.id
    new_file.visibility = uploaded_file['visibility']

    session.add(new_file)

    return serializers.serialize_rfile(session, new_file)


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
    max_date = time.time() + 3651 *  86400
    max_date = max_date - max_date % 86400
    expiration_date = expiration_date / 1000
    expiration_date = expiration_date if expiration_date < max_date else max_date
    expiration_date = datetime.utcfromtimestamp(expiration_date)

    min_date = time.time() + 91 * 86400
    min_date = min_date - min_date % 86400
    min_date = datetime.utcfromtimestamp(min_date)
    if itip.expiration_date <= min_date:
        min_date = itip.expiration_date

    if expiration_date >= min_date:
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

    if itip.crypto_tip_pub_key and value and key in ['label']:
        value = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, value))

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
def create_identityaccessrequest(session, tid, user_id, user_cc, rtip_id, request):
    """
    Transaction for the creation of notifications related to identity access requests
    :param session: An ORM session
    :param tid: A tenant ID of the user issuing the request
    :param user_id: A user ID of the user issuing the request
    :param rtip_id: A rtip_id ID of the rtip involved in the request
    :param request: The request data
    """
    user, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    crypto_tip_prv_key = GCE.asymmetric_decrypt(user_cc, base64.b64decode(rtip.crypto_tip_prv_key))

    iar = models.IdentityAccessRequest()
    iar.internaltip_id = itip.id
    iar.request_user_id = user.id
    iar.request_motivation = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, request['request_motivation']))
    session.add(iar)
    session.flush()

    custodians = 0
    for custodian in session.query(models.User).filter(models.User.tid == tid, models.User.role == 'custodian'):
        iarc = models.IdentityAccessRequestCustodian()
        iarc.identityaccessrequest_id = iar.id
        iarc.custodian_id = custodian.id
        iarc.crypto_tip_prv_key = base64.b64encode(GCE.asymmetric_encrypt(custodian.crypto_pub_key, crypto_tip_prv_key))
        session.add(iarc)
        custodians += 1

    if not custodians:
        iar.reply_date = datetime_now()
        iar.reply_user_id = user_id
        iar.reply = 'authorized'

    db_create_identityaccessrequest_notifications(session, itip, rtip, iar)

    return serializers.serialize_identityaccessrequest(session, iar)


@transact
def create_comment(session, tid, user_id, rtip_id, content, visibility=0):
    """
    Transaction for registering a new comment
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user id of the user creating the comment
    :param rtip_id: The rtip associated to the comment to be created
    :param content: The content of the comment
    :param visibility: The visibility type of the comment
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
    comment.visibility = visibility
    session.add(comment)
    session.flush()

    ret = serializers.serialize_comment(session, comment)
    ret['content'] = content
    return ret


def redact_file(session, tid, user_id, file_id):
    """
    Transaction for deleting a wbfile
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param file_id: The file ID of the wbfile to be deleted
    """

    wbfile = (
        session.query(models.ReceiverFile)
        .filter(models.User.id == user_id, models.ReceiverFile.filename == file_id,
                models.ReceiverTip.receiver_id == models.User.id,
                models.ReceiverTip.internaltip_id == models.InternalTip.id, models.InternalTip.tid == tid)
        .first()
    )

    if wbfile:
        receiver_file_list = session.query(models.ReceiverFile).filter(
            models.ReceiverFile.filename == wbfile.filename).all()
        internal_file_list = session.query(models.InternalFile).filter(
            models.InternalFile.filename == wbfile.filename).all()
        all_files_to_delete = receiver_file_list + internal_file_list
        for file in all_files_to_delete:
            session.delete(file)


def delete_wbfile(session, tid, user_id, file_id):
    """
    Transaction for deleting a wbfile
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param file_id: The file ID of the rfile to be deleted
    """
    itips_ids = [x[0] for x in session.query(models.InternalTip.id)
    .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
            models.ReceiverTip.receiver_id == user_id,
            models.InternalTip.tid == tid)]

    wbfile = (
        session.query(models.WhistleblowerFile)
        .filter(models.WhistleblowerFile.id == file_id,
                models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id,
                models.ReceiverTip.internaltip_id.in_(itips_ids), models.InternalTip.tid == tid)
        .first()
    )

    if wbfile:
        session.delete(wbfile)

@transact
def delete_redaction(session, tid, user_id, rtip_id, id):
    """
    Transaction for deleting a wbfile
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param rtip_id: The rtip_id performing the operation
    :param id: The ID of the redaction to be deleted
    """
    itips_ids = [x[0] for x in session.query(models.InternalTip.id)
                                      .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                              models.ReceiverTip.receiver_id == user_id,
                                              models.InternalTip.tid == tid)]

    redaction = (
      session.query(models.Redaction)
      .filter(models.Redaction.id == id, models.ReceiverTip.internaltip_id.in_(itips_ids), models.InternalTip.tid == tid)
      .first()
    )

    if redaction:
        session.delete(redaction)

@transact
def redact_file(session, tid, user_id, rtip_id, id):
  """
    Transaction for deleting a wbfile
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param rtip_id: The rtip_id performing the operation
    :param id: The ID of the redaction to be deleted
    """
  itips_ids = [x[0] for x in session.query(models.InternalTip.id)
                                    .filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                            models.ReceiverTip.receiver_id == user_id,
                                            models.InternalTip.tid == tid)]

  redaction = session.query(models.Redaction) \
                   .filter(models.Redaction.id == id, models.ReceiverTip.internaltip_id.in_(itips_ids), models.InternalTip.tid == tid) \
                   .first()

  if redaction:
    redact_file(tid, user_id, redaction.reference_id)
    session.delete(redaction)


@transact
def create_redaction(session, tid, user_id, rtip_id, content):
    """
    Transaction for registering a new redaction
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user id of the user creating the redaction
    :param rtip_id: The rtip associated with the redaction to be created
    :param content: The content of the redaction
    :return: A serialized descriptor of the redaction
    """
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()

    redaction_content = {}
    if itip.crypto_tip_pub_key:
        if isinstance(content, dict):
            redaction_content = content
        else:
            content_str = content.get('content', str(content))
            content_bytes = content_str.encode()
            redaction_content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content_bytes)).decode()

    tempRedaction = [value for value in redaction_content.get('temporary_redaction', {}).values()]
    permanentRedaction = redaction_content.get('permanent_redaction', [])

    redaction = models.Redaction()
    redaction.internaltip_id = itip.id
    redaction.temporary_redaction = tempRedaction
    redaction.update_date = datetime_now()
    redaction.reference_id = redaction_content.get('reference_id', '')
    redaction.permanent_redaction = permanentRedaction
    session.add(redaction)
    session.flush()

    ret = serializers.serialize_redaction(session, redaction)
    ret['redaction'] = content
    return ret


@transact
def update_tip_redaction(session, tid, user_id, rtip_id, id, data, tip_data):
    """
    Transaction for updating tip redaction

    :param session: An ORM session
    :param tid: The tenant ID
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: The ID of the rtip accessed by the user
    :param id: The ID of the redaction to be updated
    :param data: The updated redaction data
    """
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    redaction_data = data.get('data', {})

    if 'content_type' in redaction_data:
        content_type = redaction_data['content_type']

        if content_type == "comment":
            model = session.query(models.Comment).get(redaction_data['reference_id'])
            db_mask_comments(session, tid, user_id, itip, id, redaction_data, tip_data, "comments", model)
        elif content_type == "answer":
            db_mask_answer(session, tid, user_id, itip, id, redaction_data, tip_data)
        else:
            print("No valid content type found")
    else:
        print("Content type not provided")
        db_update_redaction(session, tid, user_id, itip, id, redaction_data)


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
          'update_status': RTipInstance.update_submission_status,
          'transfer': RTipInstance.transfer_tip

        }

    def set_tip_val(self, req_args, rtip_id, *args, **kwargs):
        value = req_args['value']
        key = req_args['key']

        if key == 'enable_notifications':
            return set_receivertip_variable(self.request.tid, self.session.user_id, rtip_id, key, value)

        return set_internaltip_variable(self.request.tid, self.session.user_id, rtip_id, key, value)

    def grant_tip_access(self, req_args, rtip_id, *args, **kwargs):
        return grant_tip_access(self.request.tid, self.session.user_id, self.session.cc, rtip_id, req_args['receiver'])

    def revoke_tip_access(self, req_args, rtip_id, *args, **kwargs):
        return revoke_tip_access(self.request.tid, self.session.user_id, rtip_id, req_args['receiver'])

    def transfer_tip(self, req_args, rtip_id, *args, **kwargs):
        return transfer_tip_access(self.request.tid, self.session.user_id, self.session.cc, rtip_id, req_args['receiver'])

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
        return create_comment(self.request.tid, self.session.user_id, rtip_id, request['content'], request['visibility'])


class RTipRedactionCollection(BaseHandler):
    """
    Interface used to handle rtip redaction
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
            'update_redaction': RTipRedactionCollection.update_redaction
        }

    def post(self, rtip_id):
        self.request.content.seek(0)
        payload = self.request.content.read().decode('utf-8')
        data = json.loads(payload)
        return create_redaction(self.request.tid, self.session.user_id, rtip_id, data)

    def put(self, rtip_id, id):
        self.request.content.seek(0)
        payload = self.request.content.read().decode('utf-8')
        data = json.loads(payload)
        return self.update_redaction(rtip_id, id, data, self.session.cc)

    def update_redaction(self, rtip_id, id, data, *args, **kwargs):
        tip_data_deferred = self.get(rtip_id)

        def handle_tip_data(tip_data):
            return update_tip_redaction(self.request.tid, self.session.user_id, rtip_id, id, data, tip_data)

        tip_data_deferred.addCallback(handle_tip_data)

    def delete(self, rtip_id, id):
        return delete_redaction(self.request.tid, self.session.user_id, rtip_id, id)


class RTipFileRedactionCollection(BaseHandler):
    """
    Interface used to handle rtip redaction
    """
    check_roles = 'receiver'

    @inlineCallbacks
    def get(self, tip_id):
        tip, crypto_tip_prv_key = yield get_rtip(self.request.tid, self.session.user_id, tip_id, self.request.language)

        if State.tenants[self.request.tid].cache.encryption and crypto_tip_prv_key:
            tip = yield deferToThread(decrypt_tip, self.session.cc, crypto_tip_prv_key, tip)

        returnValue(tip)

    def delete(self, rtip_id, id):
        return redact_file(self.request.tid, self.session.user_id, rtip_id, id)


class WhistleblowerFileDownload(BaseHandler):
    """
    This handler exposes wbfiles for download.
    """
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @transact
    def download_wbfile(self, session, tid, user_id, file_id):
        ifile, wbfile, rtip, pgp_key = db_get(session,
                                             (models.InternalFile,
                                              models.WhistleblowerFile,
                                              models.ReceiverTip,
                                              models.User.pgp_key_public),
                                             (models.ReceiverTip.receiver_id == models.User.id,
                                              models.ReceiverTip.id == models.WhistleblowerFile.receivertip_id,
                                              models.InternalFile.id == models.WhistleblowerFile.internalfile_id,
                                              models.WhistleblowerFile.id == file_id,
                                              models.User.id == user_id))

        if wbfile.access_date == datetime_null():
            wbfile.access_date = datetime_now()

        log.debug("Download of file %s by receiver %s" %
                  (wbfile.internalfile_id, rtip.receiver_id))

        return ifile.name, ifile.id, wbfile.id, rtip.crypto_tip_prv_key, rtip.deprecated_crypto_files_prv_key, pgp_key

    @inlineCallbacks
    def get(self, wbfile_id):
        name, ifile_id, wbfile_id, tip_prv_key, tip_prv_key2, pgp_key = yield self.download_wbfile(self.request.tid, self.session.user_id, wbfile_id)

        filelocation = os.path.join(self.state.settings.attachments_path, wbfile_id)
        if not os.path.exists(filelocation):
            filelocation = os.path.join(self.state.settings.attachments_path, ifile_id)

        directory_traversal_check(self.state.settings.attachments_path, filelocation)
        self.check_file_presence(filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.session.cc, base64.b64decode(tip_prv_key))

            if tip_prv_key2:
                files_prv_key = GCE.asymmetric_decrypt(self.session.cc, base64.b64decode(tip_prv_key2))
            else:
                files_prv_key = tip_prv_key

            name = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(name.encode())).decode()

            filelocation = GCE.streaming_encryption_open('DECRYPT', files_prv_key, filelocation)

        yield self.write_file_as_download(name, filelocation, pgp_key)


class ReceiverFileHandler(BaseHandler):
    """
    Receiver interface to upload a file intended for the whistleblower
    """
    check_roles = 'receiver'
    upload_handler = True

    @inlineCallbacks
    def post(self, rtip_id):
        yield register_rfile_on_db(self.request.tid, self.session.user_id, rtip_id, self.uploaded_file)

        log.debug("Recorded new ReceiverFile %s",
                  self.uploaded_file['name'])


class RTipWBFileHandler(BaseHandler):
    """
    This handler lets the recipient download and delete rfiles, which are files
    intended for delivery to the whistleblower.
    """
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @transact
    def download_rfile(self, session, tid, user_id, file_id):
        rfile, wbtip, pgp_key = db_get(session,
                                        (models.ReceiverFile,
                                         models.InternalTip,
                                         models.User.pgp_key_public),
                                        (models.User.id == user_id,
                                         models.User.id == models.ReceiverTip.receiver_id,
                                         models.ReceiverFile.id == file_id,
                                         models.ReceiverFile.internaltip_id == models.InternalTip.id))

        rtip = session.query(models.ReceiverTip) \
                      .filter(models.ReceiverTip.receiver_id == self.session.user_id,
                              models.ReceiverTip.internaltip_id == wbtip.id).one_or_none()
        if not rtip:
            raise errors.ResourceNotFound

        return rfile.name, rfile.id, base64.b64decode(rtip.crypto_tip_prv_key), pgp_key

    @inlineCallbacks
    def get(self, rfile_id):
        name, filename, tip_prv_key, pgp_key = yield self.download_rfile(self.request.tid, self.session.user_id, rfile_id)

        filelocation = os.path.join(self.state.settings.attachments_path, filename)
        if not os.path.exists(filelocation):
            filelocation = os.path.join(self.state.settings.attachments_path, filename)

        filelocation = os.path.join(self.state.settings.attachments_path, filename)
        directory_traversal_check(self.state.settings.attachments_path, filelocation)
        self.check_file_presence(filelocation)

        if tip_prv_key:
            tip_prv_key = GCE.asymmetric_decrypt(self.session.cc, tip_prv_key)
            name = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(name.encode())).decode()
            filelocation = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, filelocation)

        yield self.write_file_as_download(name, filelocation, pgp_key)

    def delete(self, file_id):
        """
        This interface allow the recipient to set the description of a ReceiverFile
        """
        return delete_rfile(self.request.tid, self.session.user_id, file_id)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    Handler responsible of the creation of identity access requests
    """
    check_roles = 'receiver'

    def post(self, rtip_id):
        request = self.validate_request(self.request.content.read(), requests.ReceiverIdentityAccessRequestDesc)

        return create_identityaccessrequest(self.request.tid,
                                            self.session.user_id,
                                            self.session.cc,
                                            rtip_id,
                                            request)
