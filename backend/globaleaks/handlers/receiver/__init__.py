# -*- coding: utf-8 -*-
#
# API handling recipient user functionalities
import base64
import json

from datetime import datetime

from sqlalchemy.sql.expression import distinct, func

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_grant_tip_access, db_revoke_tip_access
from globaleaks.models import serializers
from globaleaks.orm import db_get, db_del, db_log, transact
from globaleaks.rest import requests, errors
from globaleaks.utils.crypto import GCE


@transact
def get_receivertips(session, tid, receiver_id, user_key, language, args={}):
    """
    Return list of submissions received by the specified receiver

    :param session: An ORM session
    :param tid: The tenant ID
    :param receiver_id: The receiver ID
    :param user_key: The user key to be used for decrypting data
    :param language: The language to be used during data serialization
    :return: A list of submissions descriptors
    """
    ret = {
      'questionnaires': {},
      'rtips': []
    }

    updated_after = datetime.fromtimestamp(int(args.get(b'updated_after', [b'0'])[0]))
    updated_before = datetime.fromtimestamp(int(args.get(b'updated_before', [b'32503680000'])[0]))

    messages_by_rtip = {}
    comments_by_itip = {}
    files_by_itip = {}

    # Fetch messages count
    for rtip_id, count in session.query(models.ReceiverTip.id,
                                        func.count(distinct(models.Message.id))) \
                                 .filter(models.ReceiverTip.receiver_id == receiver_id,
                                         models.Message.receivertip_id == models.ReceiverTip.id) \
                                 .group_by(models.ReceiverTip.id):
        messages_by_rtip[rtip_id] = count

    # Fetch comments count
    for itip_id, count in session.query(models.InternalTip.id,
                                        func.count(distinct(models.Comment.id))) \
                                 .filter(models.ReceiverTip.receiver_id == receiver_id,
                                         models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                         models.Comment.internaltip_id == models.InternalTip.id) \
                                 .group_by(models.InternalTip.id):
        comments_by_itip[itip_id] = count

    # Fetch files count
    for itip_id, count in session.query(models.InternalTip.id,
                                        func.count(distinct(models.InternalFile.id))) \
                                 .filter(models.ReceiverTip.receiver_id == receiver_id,
                                         models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                         models.InternalFile.internaltip_id == models.InternalTip.id) \
                                 .group_by(models.InternalTip.id):
        files_by_itip[itip_id] = count

    # Fetch rtip, internaltip and associated questionnaire schema
    rtips_ids = {}
    for rtip, itip, answers, aqs in session.query(models.ReceiverTip,
                                                  models.InternalTip,
                                                  models.InternalTipAnswers,
                                                  models.ArchivedSchema) \
                                           .filter(models.ReceiverTip.receiver_id == receiver_id,
                                                   models.InternalTip.update_date >= updated_after,
                                                   models.InternalTip.update_date <= updated_before,
                                                   models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                                   models.InternalTipAnswers.internaltip_id == models.ReceiverTip.internaltip_id,
                                                   models.InternalTipAnswers.questionnaire_hash == models.ArchivedSchema.hash) \
                                           .order_by(models.InternalTipAnswers.creation_date.asc()):
        if rtip.id in rtips_ids:
            continue

        rtips_ids[rtip.id] = True

        answers = answers.answers
        if itip.crypto_tip_pub_key:
            tip_key = GCE.asymmetric_decrypt(user_key, base64.b64decode(rtip.crypto_tip_prv_key))
            answers = json.loads(GCE.asymmetric_decrypt(tip_key, base64.b64decode(answers.encode())).decode())

        if aqs.hash not in ret['questionnaires']:
            ret['questionnaires'][aqs.hash] = serializers.serialize_archived_questionnaire_schema(aqs.schema, language)

        ret['rtips'].append({
            'id': rtip.id,
            'itip_id': itip.id,
            'creation_date': itip.creation_date,
            'access_date': rtip.access_date,
            'last_access': itip.last_access,
            'update_date': itip.update_date,
            'expiration_date': itip.expiration_date,
            'reminder_date': itip.reminder_date,
            'progressive': itip.progressive,
            'important': itip.important,
            'label': itip.label,
            'updated': rtip.last_access < itip.update_date,
            'context_id': itip.context_id,
            'tor': itip.tor,
            'questionnaire': aqs.hash,
            'answers': answers,
            'score': itip.score,
            'status': itip.status,
            'substatus': itip.substatus,
            'file_count': files_by_itip.get(itip.id, 0),
            'comment_count': comments_by_itip.get(itip.id, 0),
            'message_count': messages_by_rtip.get(rtip.id, 0)
        })

    return ret


@transact
def perform_tips_operation(session, tid, user_id, user_cc, operation, args):
    """
    Transaction for performing operation on submissions (postpone/delete)

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A recipient ID
    :param user_cc: A recipient crypto key
    :param operation: An operation command (postpone/delete)
    :param args: The operation arguments
    """
    receiver = db_get(session, models.User, models.User.id == user_id)

    result = session.query(models.InternalTip, models.ReceiverTip) \
                                 .filter(models.ReceiverTip.receiver_id == user_id,
                                         models.ReceiverTip.id.in_(args['rtips']),
                                         models.InternalTip.id == models.ReceiverTip.internaltip_id)

    if operation == 'delete' and receiver.can_delete_submission:
        itip_ids = []

        for itip, _ in result:
            itip_ids.append(itip.id)
            db_log(session, tid=tid, type='delete_report', user_id=user_id, object_id=itip.id)

        db_del(session, models.InternalTip, models.InternalTip.id.in_(itip_ids))

    elif operation == 'grant' and receiver.can_grant_access_to_reports:
        for _, rtip in result:
            db_grant_tip_access(session, tid, user_id, user_cc, rtip.id, args['receiver'])

    elif operation == 'revoke' and receiver.can_grant_access_to_reports:
        for _, rtip in result:
            db_revoke_tip_access(session, tid, user_id, rtip.id, args['receiver'])

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
                                self.request.language,
                                self.request.args)


class Operations(BaseHandler):
    """
    Handler that enables to issue operations on submissions
    """
    check_roles = 'receiver'

    def put(self):
        request = self.validate_request(self.request.content.read(), requests.OpsDesc)

        if request['operation'] not in ['delete', 'grant', 'revoke']:
            raise errors.ForbiddenOperation

        return perform_tips_operation(self.request.tid,
                                      self.session.user_id,
                                      self.session.cc,
                                      request['operation'],
                                      request['args'])
