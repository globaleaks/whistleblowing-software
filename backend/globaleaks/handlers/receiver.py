# -*- coding: utf-8 -*-
#
# API handling recipient user functionalities
import base64
import json

from sqlalchemy.sql.expression import func, distinct

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_postpone_expiration, db_delete_itips
from globaleaks.handlers.submission import db_serialize_archived_preview_schema
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.crypto import GCE
from globaleaks.utils.utility import datetime_to_ISO8601


@transact
def get_receivertips(session, tid, receiver_id, user_key, language):
    """
    Return list of submissions received by the specified receiver

    :param session: An ORM session
    :param tid: The tenant ID
    :param receiver_id: The receiver ID
    :param user_key: The user key to be used for decrypting data
    :param language: The language to be used during data serialization
    :return: A list of submissions descriptors
    """
    rtip_summary_list = []

    rtip_ids = []
    itip_ids = []

    messages_by_rtip = {}
    comments_by_itip = {}
    internalfiles_by_itip = {}

    # Fetch rtip, internaltip and associated questionnaire schema
    for rtip, itip, aqs in session.query(models.ReceiverTip,
                                         models.InternalTip,
                                         models.ArchivedSchema) \
                                  .filter(models.ReceiverTip.receiver_id == receiver_id,
                                          models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                          models.InternalTipAnswers.internaltip_id == models.InternalTip.id,
                                          models.ArchivedSchema.hash == models.InternalTipAnswers.questionnaire_hash,
                                          models.InternalTip.tid == tid):
        rtip_ids.append(rtip.id)
        itip_ids.append(itip.id)

        preview = itip.preview

        if itip.crypto_tip_pub_key:
            tip_key = GCE.asymmetric_decrypt(user_key, base64.b64decode(rtip.crypto_tip_prv_key))

            preview = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(itip.preview.encode())).decode())

        data = {
            'id': rtip.id,
            'itip_id': itip.id,
            'creation_date': datetime_to_ISO8601(itip.creation_date),
            'last_access': datetime_to_ISO8601(rtip.last_access),
            'wb_last_access': datetime_to_ISO8601(itip.wb_last_access),
            'update_date': datetime_to_ISO8601(itip.update_date),
            'expiration_date': datetime_to_ISO8601(itip.expiration_date),
            'progressive': itip.progressive,
            'new': rtip.access_counter == 0 or rtip.last_access < itip.update_date,
            'context_id': itip.context_id,
            'access_counter': rtip.access_counter,
            'https': itip.https,
            'preview_schema': db_serialize_archived_preview_schema(aqs.preview, language),
            'preview': preview,
            'score': itip.total_score,
            'label': rtip.label,
            'status': itip.status,
            'substatus': itip.substatus
        }

        if State.tenant_cache[tid].enable_private_labels:
            data['label'] = rtip.label
        else:
            data['label'] = itip.label

        rtip_summary_list.append(data)

    # Fetch messages count
    for rtip_id, count in session.query(models.ReceiverTip.id,
                                        func.count(distinct(models.Message.id))) \
                                 .filter(models.Message.receivertip_id == models.ReceiverTip.id,
                                         models.ReceiverTip.id.in_(rtip_ids)) \
                                 .group_by(models.ReceiverTip.id):
        messages_by_rtip[rtip_id] = count

    # Fetch comments count
    for itip_id, count in session.query(models.InternalTip.id,
                                        func.count(distinct(models.Comment.id))) \
                                 .filter(models.Comment.internaltip_id == models.InternalTip.id,
                                         models.InternalTip.id.in_(itip_ids)) \
                                 .group_by(models.InternalTip.id):
        comments_by_itip[itip_id] = count

    # Fetch attachment count
    for itip_id, count in session.query(models.InternalTip.id,
                                        func.count(distinct(models.InternalFile.id))) \
                                 .filter(models.InternalFile.internaltip_id == models.InternalTip.id,
                                         models.InternalTip.id.in_(itip_ids)) \
                                 .group_by(models.InternalTip.id):
        internalfiles_by_itip[itip_id] = count

    for elem in rtip_summary_list:
        elem['file_count'] = internalfiles_by_itip.get(elem['itip_id'], 0)
        elem['comment_count'] = comments_by_itip.get(elem['itip_id'], 0)
        elem['message_count'] = messages_by_rtip.get(elem['id'], 0)

    return rtip_summary_list


@transact
def perform_tips_operation(session, tid, receiver_id, operation, rtips_ids):
    """
    Transaction for performing operation on submissions (postpone/delete)

    :param session: An ORM session
    :param tid: A tenant ID
    :param receiver_id: A recipient ID
    :param operation: An operation command (postpone/delete)
    :param rtips_ids: The set of submissions on which performing the specified operation
    """
    receiver = models.db_get(session, models.User,
                             models.User.id == receiver_id)

    can_postpone_expiration = State.tenant_cache[tid].can_postpone_expiration or receiver.can_postpone_expiration
    can_delete_submission = State.tenant_cache[tid].can_delete_submission or receiver.can_delete_submission

    itips = session.query(models.InternalTip) \
                   .filter(models.ReceiverTip.receiver_id == receiver_id,
                           models.ReceiverTip.id.in_(rtips_ids),
                           models.InternalTip.id == models.ReceiverTip.internaltip_id,
                           models.InternalTip.tid == tid)

    if operation == 'postpone' and can_postpone_expiration:
        for itip in itips:
            db_postpone_expiration(session, itip)

    elif operation == 'delete' and can_delete_submission:
        db_delete_itips(session, [itip.id for itip in itips])

    else:
        raise errors.ForbiddenOperation


class TipsCollection(BaseHandler):
    """

    Handler dealing with submissions fetch
    """
    check_roles = 'receiver'

    def get(self):
        return get_receivertips(self.request.tid,
                                    self.current_user.user_id,
                                    self.current_user.cc,
                                    self.request.language)


class TipsOperations(BaseHandler):
    """
    Handler that enables to issue operations on submissions
    """
    check_roles = 'receiver'

    def put(self):
        request = self.validate_message(self.request.content.read(), requests.ReceiverOperationDesc)

        if request['operation'] not in ['postpone', 'delete']:
            raise errors.ForbiddenOperation

        return perform_tips_operation(self.request.tid,
                                      self.current_user.user_id,
                                      request['operation'],
                                      request['rtips'])
