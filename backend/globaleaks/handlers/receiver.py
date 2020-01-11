# -*- coding: utf-8 -*-
#
# API handling recipient user functionalities
import base64
import json

from sqlalchemy.sql.expression import func, distinct

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_postpone_expiration_date, db_delete_itip
from globaleaks.handlers.submission import db_serialize_archived_preview_schema
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.crypto import GCE
from globaleaks.utils.utility import datetime_to_ISO8601


@transact
def get_receivertip_list(session, tid, receiver_id, user_key, language):
    rtip_summary_list = []

    rtips = session.query(models.ReceiverTip).filter(models.ReceiverTip.receiver_id == receiver_id,
                                                     models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                                     models.InternalTip.tid == tid)

    itips_ids = [rtip.internaltip_id for rtip in rtips]

    if not itips_ids:
        return []

    itips_by_id = {}
    ps_by_itip = {}
    comments_by_itip = {}
    internalfiles_by_itip = {}
    messages_by_rtip = {}


    for itip, aqs in session.query(models.InternalTip, models.ArchivedSchema) \
                           .filter(models.InternalTip.id.in_(itips_ids),
                                   models.ArchivedSchema.hash == models.InternalTipAnswers.questionnaire_hash,
                                   models.InternalTipAnswers.internaltip_id == models.InternalTip.id,
                                   models.InternalTip.tid == tid):
        itips_by_id[itip.id] = itip
        ps_by_itip[itip.id] = aqs.preview

    result = session.query(models.ReceiverTip.id, func.count(distinct(models.Message.id))) \
                    .filter(models.ReceiverTip.receiver_id == receiver_id,
                            models.ReceiverTip.id == models.Message.receivertip_id,
                            models.InternalTip.id == models.ReceiverTip.internaltip_id).group_by(models.ReceiverTip.id)
    for rtip_id, count in result:
        messages_by_rtip[rtip_id] = count

    result = session.query(models.InternalTip.id, func.count(distinct(models.Comment.id))) \
                    .filter(models.Comment.internaltip_id == models.InternalTip.id,
                            models.InternalTip.id.in_(itips_ids)).group_by(models.InternalTip.id)
    for itip_id, count in result:
        comments_by_itip[itip_id] = count

    result = session.query(models.InternalTip.id, func.count(distinct(models.InternalFile.id))) \
                    .filter(models.InternalFile.internaltip_id == models.InternalTip.id,
                            models.InternalTip.id.in_(itips_ids)).group_by(models.InternalTip.id)
    for itip_id, count in result:
        internalfiles_by_itip[itip_id] = count

    for rtip in rtips:
        itip = itips_by_id[rtip.internaltip_id]

        preview = itip.preview

        if itip.crypto_tip_pub_key:
            tip_key = GCE.asymmetric_decrypt(user_key, rtip.crypto_tip_prv_key)

            preview = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(itip.preview.encode())).decode())

        rtip_summary_list.append({
            'id': rtip.id,
            'creation_date': datetime_to_ISO8601(itip.creation_date),
            'last_access': datetime_to_ISO8601(rtip.last_access),
            'wb_last_access': datetime_to_ISO8601(itip.wb_last_access),
            'update_date': datetime_to_ISO8601(itip.update_date),
            'expiration_date': datetime_to_ISO8601(itip.expiration_date),
            'progressive': itip.progressive,
            'new': rtip.access_counter == 0 or rtip.last_access < itip.update_date,
            'context_id': itip.context_id,
            'access_counter': rtip.access_counter,
            'file_count': internalfiles_by_itip.get(itip.id, 0),
            'comment_count': comments_by_itip.get(itip.id, 0),
            'message_count': messages_by_rtip.get(rtip.id, 0),
            'https': itip.https,
            'preview_schema': db_serialize_archived_preview_schema(ps_by_itip[rtip.internaltip_id], language),
            'preview': preview,
            'score': itip.total_score,
            'label': rtip.label,
            'status': itip.status,
            'substatus': itip.substatus
        })

    return rtip_summary_list


@transact
def perform_tips_operation(session, tid, receiver_id, operation, rtips_ids):
    receiver = models.db_get(session, models.User,
                             models.User.id == receiver_id)

    can_postpone_expiration = State.tenant_cache[tid].can_postpone_expiration or receiver.can_postpone_expiration
    can_delete_submission = State.tenant_cache[tid].can_delete_submission or receiver.can_delete_submission

    for itip in session.query(models.InternalTip) \
                       .filter(models.ReceiverTip.receiver_id == receiver_id,
                               models.ReceiverTip.id.in_(rtips_ids),
                               models.InternalTip.id == models.ReceiverTip.internaltip_id,
                               models.InternalTip.tid == tid):
        if operation == 'postpone' and can_postpone_expiration:
            db_postpone_expiration_date(session, tid, itip)

        elif operation == 'delete' and can_delete_submission:
            db_delete_itip(session, itip)

        else:
            raise errors.ForbiddenOperation


class TipsCollection(BaseHandler):
    """
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips
    """
    check_roles = 'receiver'

    def get(self):
        return get_receivertip_list(self.request.tid,
                                    self.current_user.user_id,
                                    self.current_user.cc,
                                    self.request.language)


class TipsOperations(BaseHandler):
    """
    This interface receive some operation (postpone or delete) and a list of
    tips to apply.
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
