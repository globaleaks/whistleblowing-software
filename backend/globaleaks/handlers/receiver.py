# -*- coding: utf-8 -*-
#
# API handling recipient user functionalities
import base64
import json

from sqlalchemy.sql.expression import distinct, func

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_postpone_expiration
from globaleaks.handlers.submission import db_serialize_archived_questionnaire_schema
from globaleaks.orm import db_get, db_del, transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.crypto import GCE


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
    files_by_itip = {}

    # Fetch rtip, internaltip and associated questionnaire schema
    for rtip, itip, answers, aqs in session.query(models.ReceiverTip,
                                                  models.InternalTip,
                                                  models.InternalTipAnswers,
                                                  models.ArchivedSchema) \
                                           .filter(models.ReceiverTip.receiver_id == receiver_id,
                                                   models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                                   models.InternalTipAnswers.internaltip_id == models.InternalTip.id,
                                                   models.ArchivedSchema.hash == models.InternalTipAnswers.questionnaire_hash,
                                                   models.InternalTip.tid == tid) \
                                           .order_by(models.InternalTip.progressive.desc(), models.InternalTipAnswers.creation_date.asc()):
        if rtip.id in rtip_ids:
            continue

        rtip_ids.append(rtip.id)
        itip_ids.append(itip.id)

        answers = answers.answers
        if itip.crypto_tip_pub_key:
            tip_key = GCE.asymmetric_decrypt(user_key, base64.b64decode(rtip.crypto_tip_prv_key))

            answers = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(answers.encode())).decode())

        data = {
            'id': rtip.id,
            'itip_id': itip.id,
            'creation_date': itip.creation_date,
            'last_access': rtip.last_access,
            'wb_last_access': itip.wb_last_access,
            'update_date': itip.update_date,
            'expiration_date': itip.expiration_date,
            'progressive': itip.progressive,
            'updated': rtip.access_counter == 0 or rtip.last_access < itip.update_date,
            'context_id': itip.context_id,
            'access_counter': rtip.access_counter,
            'https': itip.https,
            'questionnaire': db_serialize_archived_questionnaire_schema(aqs.schema, language),
            'answers': answers,
            'score': itip.total_score,
            'status': itip.status,
            'substatus': itip.substatus
        }

        if State.tenant_cache[tid].enable_private_annotations:
            data['important'] = rtip.important
            data['label'] = rtip.label
        else:
            data['important'] = itip.important
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
        files_by_itip[itip_id] = count

    for elem in rtip_summary_list:
        elem['file_count'] = files_by_itip.get(elem['itip_id'], 0)
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
    receiver = db_get(session, models.User, models.User.id == receiver_id)

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
        itip_ids = [itip.id for itip in itips]

        for itip_id in itip_ids:
            State.log(tid=tid, type='delete_report', user_id=receiver_id, object_id=itip_id)

        db_del(session, models.InternalTip, models.InternalTip.id.in_(itip_ids))

    else:
        raise errors.ForbiddenOperation


class TipsCollection(BaseHandler):
    """

    Handler dealing with submissions fetch
    """
    check_roles = 'receiver'

    def get(self):
        return get_receivertips(self.request.tid,
                                self.session.user_id,
                                self.session.cc,
                                self.request.language)

class Operations(BaseHandler):
    """
    Handler that enables to issue operations on submissions
    """
    check_roles = 'receiver'

    def put(self):
        request = self.validate_message(self.request.content.read(), requests.ReceiverOperationDesc)

        if request['operation'] not in ['delete', 'postpone']:
            raise errors.ForbiddenOperation

        return perform_tips_operation(self.request.tid,
                                      self.session.user_id,
                                      request['operation'],
                                      request['rtips'])
