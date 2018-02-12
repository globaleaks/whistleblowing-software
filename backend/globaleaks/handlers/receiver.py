# -*- coding: utf-8 -*-
#
# API handling recipient user functionalities
from sqlalchemy.sql.expression import func, distinct

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_postpone_expiration_date, db_delete_itip
from globaleaks.handlers.submission import db_serialize_archived_preview_schema
from globaleaks.handlers.user import db_user_update_user
from globaleaks.handlers.user import user_serialize_user
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.utility import datetime_to_ISO8601


def receiver_serialize_receiver(session, tid, receiver, user, language):
    user = session.query(models.User).filter(models.User.id == receiver.id, models.User.tid == tid).one_or_none()

    contexts = [x[0] for x in session.query(models.ReceiverContext.context_id) \
                                     .filter(models.ReceiverContext.receiver_id == receiver.id, \
                                             models.User.id == receiver.id,
                                             models.User.tid == tid)]

    ret_dict = user_serialize_user(session, user, language)

    ret_dict.update({
        'can_postpone_expiration': State.tenant_cache[tid].can_postpone_expiration or receiver.can_postpone_expiration,
        'can_delete_submission': State.tenant_cache[tid].can_delete_submission or receiver.can_delete_submission,
        'can_grant_permissions': State.tenant_cache[tid].can_grant_permissions or receiver.can_grant_permissions,
        'tip_notification': receiver.tip_notification,
        'contexts': contexts
    })

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


@transact
def get_receiver_settings(session, tid, receiver_id, language):
    receiver, user = session.query(models.Receiver, models.User) \
                            .filter(models.Receiver.id == receiver_id,
                                    models.User.id == receiver_id,
                                    models.User.tid == tid).one()

    return receiver_serialize_receiver(session, tid, receiver, user, language)


@transact
def update_receiver_settings(session, state, tid, receiver_id, request, language):
    db_user_update_user(session, state, tid, receiver_id, request)

    receiver, user = session.query(models.Receiver, models.User). \
                           filter(models.Receiver.id == receiver_id,
                                  models.User.id == receiver_id,
                                  models.User.tid == tid).one_or_none()

    receiver.tip_notification = request['tip_notification']

    return receiver_serialize_receiver(session, tid, receiver, user, language)


@transact
def get_receivertip_list(session, tid, receiver_id, language):
    rtip_summary_list = []

    rtips = session.query(models.ReceiverTip).filter(models.ReceiverTip.receiver_id == receiver_id,
                                                     models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                                     models.InternalTip.tid == tid)

    itips_ids = [rtip.internaltip_id for rtip in rtips]

    if not itips_ids:
        return []

    itips_by_id = {}
    aqs_by_itip = {}
    comments_by_itip = {}
    internalfiles_by_itip = {}
    messages_by_rtip = {}

    for itip, archivedschema in session.query(models.InternalTip, models.ArchivedSchema) \
                                     .filter(models.InternalTip.id.in_(itips_ids),
                                             models.ArchivedSchema.hash == models.InternalTip.questionnaire_hash,
                                             models.InternalTip.tid == tid):
        itips_by_id[itip.id] = itip
        aqs_by_itip[itip.id] = archivedschema

    result = session.query(models.ReceiverTip.id, func.count(distinct(models.ReceiverTip.id))) \
                    .filter(models.ReceiverTip.receiver_id == receiver_id,
                            models.ReceiverTip.id == models.Message.receivertip_id,
                            models.InternalTip.id == models.ReceiverTip.internaltip_id,
                            models.InternalTip.tid == tid).group_by(models.ReceiverTip)
    for rtip_id, count in result:
        messages_by_rtip[rtip_id] = count

    result = session.query(models.InternalTip.id, func.count(distinct(models.InternalTip.id))) \
                    .filter(models.InternalTip.id.in_(itips_ids),
                            models.InternalTip.id == models.Comment.internaltip_id,
                            models.InternalTip.tid == tid).group_by(models.InternalTip)
    for itip_id, count in result:
        comments_by_itip[itip_id] = count

    result = session.query(models.InternalTip.id, func.count(distinct(models.InternalTip.id))) \
                    .filter(models.InternalTip.id.in_(itips_ids),
                            models.InternalTip.id == models.InternalFile.internaltip_id,
                            models.InternalTip.tid == tid).group_by(models.InternalTip)
    for itip_id, count in result:
        internalfiles_by_itip[itip_id] = count

    for rtip in rtips:
        internaltip = itips_by_id[rtip.internaltip_id]
        archivedschema = aqs_by_itip[rtip.internaltip_id]

        rtip_summary_list.append({
            'id': rtip.id,
            'creation_date': datetime_to_ISO8601(internaltip.creation_date),
            'last_access': datetime_to_ISO8601(rtip.last_access),
            'wb_last_access': datetime_to_ISO8601(internaltip.wb_last_access),
            'update_date': datetime_to_ISO8601(internaltip.update_date),
            'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
            'progressive': internaltip.progressive,
            'new': rtip.access_counter == 0 or rtip.last_access < internaltip.update_date,
            'context_id': internaltip.context_id,
            'access_counter': rtip.access_counter,
            'file_counter': internalfiles_by_itip.get(internaltip.id, 0),
            'comment_counter': comments_by_itip.get(internaltip.id, 0),
            'message_counter': messages_by_rtip.get(rtip.id, 0),
            'https': internaltip.https,
            'preview_schema': db_serialize_archived_preview_schema(session, archivedschema.preview, language),
            'preview': internaltip.preview,
            'total_score': internaltip.total_score,
            'label': rtip.label
        })

    return rtip_summary_list


@transact
def perform_tips_operation(session, tid, receiver_id, operation, rtips_ids):
    receiver = session.query(models.Receiver).filter(models.Receiver.id == receiver_id).one()

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

class ReceiverInstance(BaseHandler):
    """
    This handler allow receivers to modify some of their fields:
        - language
        - password
        - notification settings
        - pgp key
    """
    check_roles = 'receiver'

    def get(self):
        return get_receiver_settings(self.request.tid,
                                     self.current_user.user_id,
                                     self.request.language)

    def put(self):
        request = self.validate_message(self.request.content.read(), requests.ReceiverReceiverDesc)

        return update_receiver_settings(self.state,
                                        self.request.tid,
                                        self.current_user.user_id,
                                        request,
                                        self.request.language)

class TipsCollection(BaseHandler):
    """
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips
    """
    check_roles = 'receiver'

    def get(self):
        return get_receivertip_list(self.request.tid,
                                    self.current_user.user_id,
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
