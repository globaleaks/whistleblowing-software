# -*- coding: utf-8 -*-
#
# Handlers dealing with tip interface for receivers (rtip)
import base64
import copy
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
def delete_masking(session, tid, user_id, id):
    """
      Transaction for deleting a wbfile
      :param session: An ORM session
      :param tid: A tenant ID
      :param rtip_id: The rtip_id performing the operation
      :param id: The ID of the masking to be deleted
      """
    itips_ids = [x[0] for x in session.query(models.InternalTip.id).filter(models.InternalTip.id == models.ReceiverTip.internaltip_id,
            models.ReceiverTip.receiver_id == user_id,
            models.InternalTip.tid == tid)]

    masking = (
        session.query(models.Masking)
        .filter(models.Masking.id == id, models.ReceiverTip.internaltip_id.in_(itips_ids),
                models.InternalTip.tid == tid)
        .first()
    )

    if masking:
        for temp_masking in masking.temporary_masking:
            if isinstance(temp_masking, dict) and temp_masking.get('file_masking_status') is True:
                delete_wbfile(tid, user_id, masking.content_id)

        session.delete(masking)


def db_update_masking(session, tid, user_id, masking, id, masking_data):
  """
    Update the masking data of a tip

    :param session: An ORM session
    :param tid: A tenant ID of the user performing the operation
    :param user_id: A user ID of the user changing the state
    :param itip_id: The ID of the Tip instance to be updated
    :param id: The object_id
    :param masking_data: The updated masking data
    """

  new_temporary_ranges = get_new_temporary_ranges(masking_data['temporary_masking'], masking.permanent_masking)
  new_temporary_ranges = merge_and_sort_ranges([], new_temporary_ranges)

  if len(new_temporary_ranges) == 0 and (not masking.permanent_masking or len(masking.permanent_masking) == 0):
      delete_masking(tid, user_id, id)
  else:
      masking.content_id = masking_data['content_id']
      masking.temporary_masking = new_temporary_ranges
      masking.mask_date = datetime.now()
      log_data = {
          'content_id': masking_data['content_id'],
          'mask_date': masking.mask_date.isoformat(),
          'temporary_masking': new_temporary_ranges
      }
      db_log(session, tid=tid, type='update_masking', user_id=user_id, object_id=id, data=log_data)


def redact_content(content, old_permanent_ranges, new_permanent_ranges):
    # Sort the ranges in descending order of 'end' values
    old_permanent_ranges.sort(key=lambda x: x['end'], reverse=True)

    # Initialize the result string with the original content
    result = content

    # Iterate through the old permanent ranges and insert asterisks
    old_permanent_ranges = sorted(old_permanent_ranges, key=lambda x: x['start'])
    new_permanent_ranges = sorted(new_permanent_ranges, key=lambda x: x['start'])
    for range in old_permanent_ranges:
        start = range['start']
        end = range['end']+1
        redaction = '*' * (end - start)

        result = result[:start] + redaction + result[end - len(redaction):]

    # Convert the modified string to a list for efficient updates
    modified_content = list(result)

    for r in new_permanent_ranges:
        start, end = r.get('start', 0), r.get('end', 0)+1

        if start < end:
            modified_content[start:end] = '*' * (end - start)

    # Join the list back to a string and remove asterisks or return a space if empty
    return ''.join(modified_content).replace('*', '') or ' '

def find_missing_ranges(old_ranges, new_ranges):
    missing_ranges = []

    for old_range in old_ranges:
        for i in range(old_range['start'], old_range['end'] + 1):
            found = False

            for new_range in new_ranges:
                if i >= new_range['start'] and i <= new_range['end']:
                    found = True
                    break

            if not found:
                if missing_ranges:
                    last_missing_range = missing_ranges[-1]
                    if i == last_missing_range['end'] + 1:
                        last_missing_range['end'] = i
                    else:
                        missing_ranges.append({'start': i, 'end': i})
                else:
                    missing_ranges.append({'start': i, 'end': i})

    return missing_ranges

def db_mask_data(session, masked_marker, temporary_ranges, permanent_ranges, masking_data, content, tid, user_id, id):
  """
    Transaction for updating masked data

    :param temporary_ranges: new permanent ranges that to be marked
    :param permanent_ranges: existing temporary ranges that are marked
    :param content: textual content to be updated
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param id: The ID of the masking to be deleted
    :param masked_marker: Object used to update masking in database
    :param id: The ID of the masking to be deleted
    """

  masked_marker.content_id = masking_data['content_id']
  masked_marker.temporary_masking = temporary_ranges
  masked_marker.mask_date = datetime.now()
  session.commit()
  masked_marker.permanent_masking = permanent_ranges
  session.commit()

  log_data = {'content': content}
  masking_log_data = {
    'temporary_masking': [],
  }

  db_log(session, tid=tid, type='update_masking', user_id=user_id, object_id=id, data=masking_log_data)

def validate_ranges(current_masking, new_masking):
    for new_range in new_masking:
        new_start, new_end = new_range['start'], new_range['end']
        is_within = False

        for current_range in current_masking:
            current_start, current_end = current_range['start'], current_range['end']
            if current_start <= new_start <= new_end <= current_end:
                is_within = True
                break

        if not is_within:
            return False

    return True


def get_new_temporary_ranges(current_masking, new_masking):
    result = []

    # Add the current masking ranges to the result list
    for range_ in current_masking:
        result.append(range_)

    # Iterate through the new masking ranges and remove overlapping ranges
    for new_range in new_masking:
        new_start, new_end = new_range['start'], new_range['end']
        updated_result = []

        # Check for overlaps with each range in the current masking
        for current_range in result:
            current_start, current_end = current_range['start'], current_range['end']

            # Case 1: No overlap, keep the current range
            if new_end < current_start or new_start > current_end:
                updated_result.append(current_range)

            # Case 2: Overlap, split the current range into two if needed
            else:
                if new_start > current_start:
                    updated_result.append({'start': current_start, 'end': new_start - 1})
                if new_end < current_end:
                    updated_result.append({'start': new_end + 1, 'end': current_end})

        result = updated_result

    return result


def merge_and_sort_ranges(list1, list2):
    list2_merged = []
    current_range = None

    if not list1 and not list2:
        return []

    for range_item in list2:
        if current_range is None:
            current_range = range_item
        elif range_item['start'] <= current_range['end'] + 1:
            current_range['end'] = max(current_range['end'], range_item['end'])
        else:
            list2_merged.append(current_range)
            current_range = range_item

    if current_range:
        list2_merged.append(current_range)

    combined_ranges = list1 + list2_merged
    combined_ranges.sort(key=lambda x: x['start'])

    merged_ranges = []
    current_range = combined_ranges[0]

    for range_item in combined_ranges[1:]:
        if range_item['start'] <= current_range['end'] + 1:
            current_range['end'] = max(current_range['end'], range_item['end'])
        else:
            merged_ranges.append(current_range)
            current_range = range_item

    merged_ranges.append(current_range)

    return merged_ranges


def db_mask_comment_messages(session, tid, user_id, itip_id, id, masking_data, tip_data, content_type, itip = None):
    masked_marker = session.query(models.Masking).get(id)
    currentMaskedContent = next((masked_content for masked_content in tip_data.get(content_type, []) if masked_content['id'] == masking_data['content_id']), None)
    currentMaskedData = next((masked_content for masked_content in tip_data['masking'] if masked_content['content_id'] == masking_data['content_id']), None)

    if currentMaskedData is not None and masked_marker is not None:

        content = redact_content(currentMaskedContent.get('content'), currentMaskedData['permanent_masking'], masking_data['permanent_masking'])
        itip.content = base64.b64encode(GCE.asymmetric_encrypt(itip_id.crypto_tip_pub_key, content)).decode()
        new_temporary_ranges = get_new_temporary_ranges(currentMaskedData['temporary_masking'], copy.deepcopy(masking_data['permanent_masking']))
        new_permanent_ranges = merge_and_sort_ranges(currentMaskedData['permanent_masking'], masking_data['permanent_masking'])
        db_mask_data(session, masked_marker, new_temporary_ranges, new_permanent_ranges, masking_data, content, tid, user_id, id)

def db_mask_answer(session, tid, user_id, itip_id, id, masking_data, tip_data):

  currentMaskedData = next((masked_content for masked_content in tip_data['masking'] if masked_content['content_id'] == masking_data['content_id']), None)

  tip_data = tip_data['questionnaires'][0]
  for key, value in tip_data['answers'].items():
    if key == masking_data['content_id']:
      content_data = value[0]

      content = redact_content(content_data['value'], currentMaskedData['permanent_masking'], masking_data['permanent_masking'])
      tip_data['answers'][key][0]['value'] = content
      masked_marker = session.query(models.Masking).get(id)

      range_valid = validate_ranges(currentMaskedData['temporary_masking'], masking_data['permanent_masking'])

      new_temporary_ranges = get_new_temporary_ranges(currentMaskedData['temporary_masking'], copy.deepcopy(masking_data['permanent_masking']))
      new_permanent_ranges = merge_and_sort_ranges(currentMaskedData['permanent_masking'], masking_data['permanent_masking'])

      if not range_valid:
        return

      db_mask_data(session, masked_marker, new_temporary_ranges, new_permanent_ranges, masking_data, content, tid, user_id, id)
      break

  _content = tip_data['answers']

  if itip_id.crypto_tip_pub_key:
    _content = base64.b64encode(GCE.asymmetric_encrypt(itip_id.crypto_tip_pub_key, json.dumps(_content, cls=JSONEncoder).encode())).decode()

  itip = session.query(models.InternalTipAnswers).filter_by(internaltip_id=currentMaskedData['internaltip_id']).first()

  if itip:
    itip.content = _content
    itip.answers = _content
    session.commit()



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
def delete_wbfile(session, tid, user_id, file_id):
    """
    Transaction for deleting a wbfile
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param file_id: The file ID of the wbfile to be deleted
    """

    wbfile = (
        session.query(models.WhistleblowerFile)
        .filter(models.User.id == user_id, models.WhistleblowerFile.internalfile_id == file_id,
                models.ReceiverTip.receiver_id == models.User.id,
                models.ReceiverTip.internaltip_id == models.InternalTip.id, models.InternalTip.tid == tid)
        .first()
    )

    if wbfile:
        receiver_file_list = session.query(models.WhistleblowerFile).filter(
            models.WhistleblowerFile.internalfile_id == wbfile.internalfile_id).all()
        internal_file_list = session.query(models.InternalFile).filter(
            models.InternalFile.id == wbfile.internalfile_id).all()
        all_files_to_delete = receiver_file_list + internal_file_list
        for file in all_files_to_delete:
            session.delete(file)



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



@transact
def create_masking(session, tid, user_id, rtip_id, content):
    _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    itip.update_date = rtip.last_access = datetime_now()
    user_data = session.query(models.User).get(user_id)
    
    if user_data and user_data.can_privilege_mask_information:
        masking_content = {}
        if itip.crypto_tip_pub_key:
            if isinstance(content, dict):
                masking_content = content
            else:
                content_str = content.get('content', str(content))
                content_bytes = content_str.encode()
                masking_content = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, content_bytes)).decode()

        tempMasking = masking_content.get('temporary_masking')
        permanentMasking = []

        masking = models.Masking()
        masking.internaltip_id = itip.id
        masking.temporary_masking = tempMasking
        masking.mask_date = datetime_now()
        masking.content_id = masking_content.get('content_id', None)
        masking.permanent_masking = permanentMasking
        session.add(masking)
        session.flush()

        ret = serializers.serialize_masking(session, masking)
        ret['masking'] = content
        return ret
    
    
def ranges_exist(list1, list2):
    if not list1:
        return True

    combined_range = {'start': float('inf'), 'end': float('-inf')}

    for d in list2:
        combined_range['start'] = min(combined_range['start'], d['start'])
        combined_range['end'] = max(combined_range['end'], d['end'])

    for d1 in list1:
        if d1['start'] >= combined_range['start'] and d1['end'] <= combined_range['end']:
            return True

    return False


@transact
def update_tip_masking(session, tid, user_id, rtip_id, id, data, tip_data):
  """
    Transaction for updating tip masking

    :param session: An ORM session
    :param tid: The tenant ID
    :param user_id: A user ID of the user performing the operation
    :param rtip_id: The ID of the rtip accessed by the user
    :param id: The ID of the masking to be updated
    :param data: The updated masking data
    """
  user_data = session.query(models.User).get(user_id)
  masking_data = data.get('data', {})

  masking = session.query(models.Masking).get(id)
  _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

  if masking and masking.internaltip_id == itip.id:

      if masking_data['operation'] == 'mask':
          if user_data and user_data.can_privilege_mask_information:
              db_update_masking(session, tid, user_id, masking, id, masking_data)

          elif user_data and user_data.can_privilege_delete_mask_information:
              if ranges_exist(masking_data['temporary_masking'], masking.temporary_masking):
                  db_update_masking(session, tid, user_id, masking, id, masking_data)

      elif user_data and user_data.can_privilege_delete_mask_information:
          _, rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

          if 'content_type' in masking_data:
              content_type = masking_data['content_type']
              if content_type == "comment":
                  model = session.query(models.Comment).get(masking_data['content_id'])
                  db_mask_comment_messages(session, tid, user_id, itip, id, masking_data, tip_data, "comments", model)
              elif content_type == "answer":
                  db_mask_answer(session, tid, user_id, itip, id, masking_data, tip_data)
          if masking_data['operation'] == 'redact':
            for temp_masking in masking.temporary_masking:
              if isinstance(temp_masking, dict) and temp_masking.get('file_masking_status', False) is True:
                session.delete(masking)

@transact
def delete_rfile(session, tid, user_id, file_id):
    """
    Transation for deleting a rfile
    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: The user ID of the user performing the operation
    :param file_id: The file ID of the rfile to be deleted
    """
    rfile = db_access_rfile(session, tid, user_id, file_id)
    session.delete(rfile)


class RTipMaskingCollection(BaseHandler):
  """
    Interface used to handle rtip masking
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
      'update_masking': RTipMaskingCollection.update_masking
    }

  def post(self, rtip_id):
    self.request.content.seek(0)
    payload = self.request.content.read().decode('utf-8')
    data = json.loads(payload)
    return create_masking(self.request.tid, self.session.user_id, rtip_id, data)

  def put(self, rtip_id, id):
    self.request.content.seek(0)
    payload = self.request.content.read().decode('utf-8')
    data = json.loads(payload)
    return self.update_masking(rtip_id, id, data, self.session.cc)

  def update_masking(self, rtip_id, id, data, *args, **kwargs):
    tip_data_deferred = self.get(rtip_id)

    def handle_tip_data(tip_data):
      return update_tip_masking(self.request.tid, self.session.user_id, rtip_id, id, data, tip_data)

    tip_data_deferred.addCallback(handle_tip_data)

  def delete(self, rtip_id, id):
    return delete_masking(self.request.tid, self.session.user_id, id)


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
            name = GCE.asymmetric_decrypt(tip_prv_key, base64.b64decode(name.encode())).decode()

            try:
                # First attempt
                filelocation = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, filelocation)
            except:
                # Second attempt
                if not tip_prv_key2:
                    raise

                files_prv_key2 = GCE.asymmetric_decrypt(self.session.cc, base64.b64decode(tip_prv_key2))
                filelocation = GCE.streaming_encryption_open('DECRYPT', files_prv_key2, filelocation)

        yield self.write_file_as_download(name, filelocation, pgp_key)


class ReceiverFileUpload(BaseHandler):
    """
    Receiver interface to upload a file intended for the whistleblower
    """
    check_roles = 'receiver'
    upload_handler = True

    def post(self, rtip_id):
        return register_rfile_on_db(self.request.tid, self.session.user_id, rtip_id, self.uploaded_file)


class ReceiverFileDownload(BaseHandler):
    """
    This handler lets the recipient download and delete rfiles, which are files
    intended for delivery to the whistleblower.
    """
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @transact
    def download_rfile(self, session, tid, user_id, file_id):
        try:
            rfile, rtip, pgp_key = db_get(session,
                                          (models.ReceiverFile,
                                           models.ReceiverTip,
                                           models.User.pgp_key_public),
                                          (models.User.id == user_id,
                                           models.User.id == models.ReceiverTip.receiver_id,
                                           models.ReceiverFile.id == file_id,
                                           models.ReceiverFile.internaltip_id == models.ReceiverTip.internaltip_id))
        except:
            raise errors.ResourceNotFound
        else:
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
