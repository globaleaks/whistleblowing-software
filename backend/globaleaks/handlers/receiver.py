# -*- coding: utf-8
# receiver
# ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from storm.expr import In, Count

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
from globaleaks.utils.utility import log, datetime_to_ISO8601


def receiver_serialize_receiver(store, tid, receiver, user, language):
    user = store.find(models.User, id=receiver.id, tid=tid).one()

    contexts = [id for id in store.find(models.ReceiverContext.context_id,
                                        models.ReceiverContext.receiver_id == receiver.id,
                                        models.ReceiverContext.tid==tid)]

    ret_dict = user_serialize_user(store, user, language)

    ret_dict.update({
        'can_postpone_expiration': State.tenant_cache[tid].can_postpone_expiration or receiver.can_postpone_expiration,
        'can_delete_submission': State.tenant_cache[tid].can_delete_submission or receiver.can_delete_submission,
        'can_grant_permissions': State.tenant_cache[tid].can_grant_permissions or receiver.can_grant_permissions,
        'tip_notification': receiver.tip_notification,
        'contexts': contexts
    })

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


@transact
def get_receiver_settings(store, tid, receiver_id, language):
    receiver, user = models.db_get(store,
                                   (models.Receiver, models.User),
                                   models.Receiver.id == receiver_id,
                                   models.User.id == receiver_id,
                                   models.User.tid == tid)

    return receiver_serialize_receiver(store, tid, receiver, user, language)


@transact
def update_receiver_settings(store, tid, receiver_id, request, language):
    db_user_update_user(store, tid, receiver_id, request)

    receiver, user = models.db_get(store,
                                   (models.Receiver, models.User),
                                   models.Receiver.id == receiver_id,
                                   models.User.id == receiver_id,
                                   models.User.tid == tid)

    receiver.tip_notification = request['tip_notification']

    return receiver_serialize_receiver(store, tid, receiver, user, language)


@transact
def get_receivertip_list(store, tid, receiver_id, language):
    rtip_summary_list = []

    rtips = store.find(models.ReceiverTip, receiver_id=receiver_id, tid=tid)
    itips_ids = [rtip.internaltip_id for rtip in rtips]

    itips_by_id = {}
    aqs_by_itip = {}
    comments_by_itip = {}
    internalfiles_by_itip = {}
    messages_by_rtip = {}

    for itip, archivedschema in store.find((models.InternalTip, models.ArchivedSchema),
                                           In(models.InternalTip.id, itips_ids),
                                           models.ArchivedSchema.hash == models.InternalTip.questionnaire_hash,
                                           models.ArchivedSchema.type == u'preview',
                                           models.InternalTip.tid == tid):
        itips_by_id[itip.id] = itip
        aqs_by_itip[itip.id] = archivedschema

    result = store.find((models.ReceiverTip.id, Count()),
                        models.ReceiverTip.receiver_id == receiver_id,
                        models.ReceiverTip.id == models.Message.receivertip_id,
                        models.ReceiverTip.tid == tid).group_by(models.ReceiverTip)
    for rtip_id, count in result:
        messages_by_rtip[rtip_id] = count

    result = store.find((models.InternalTip.id, Count()),
                        In(models.InternalTip.id, itips_ids),
                        models.InternalTip.id == models.Comment.internaltip_id,
                        models.InternalTip.tid == tid).group_by(models.InternalTip)
    for itip_id, count in result:
        comments_by_itip[itip_id] = count

    result = store.find((models.InternalTip.id, Count()),
                        In(models.InternalTip.id, itips_ids),
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
            'tor2web': internaltip.tor2web,
            'preview_schema': db_serialize_archived_preview_schema(store, archivedschema, language),
            'preview': internaltip.preview,
            'total_score': internaltip.total_score,
            'label': rtip.label
        })

    return rtip_summary_list


@transact
def perform_tips_operation(store, tid, receiver_id, operation, rtips_ids):
    receiver = store.find(models.Receiver, models.Receiver.id == receiver_id).one()

    for itip in store.find(models.InternalTip,
                           models.ReceiverTip.receiver_id == receiver_id,
                           In(models.ReceiverTip.id, rtips_ids),
                           models.InternalTip.id == models.ReceiverTip.internaltip_id,
                           tid=tid):

        if operation == 'postpone':
            can_postpone_expiration = State.tenant_cache[tid].can_postpone_expiration or receiver.can_postpone_expiration
            if not can_postpone_expiration:
                raise errors.ForbiddenOperation

            db_postpone_expiration_date(store, tid, itip)

        elif operation == 'delete':
            can_delete_submission = State.tenant_cache[tid].can_delete_submission or receiver.can_delete_submission
            if not can_delete_submission:
                raise errors.ForbiddenOperation

            db_delete_itip(store, tid, itip)

    log.debug("Multiple %s of %d Tips completed" % (operation, len(rtips_ids)))


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
        """
        Parameters: None
        Response: ReceiverReceiverDesc
        """
        return get_receiver_settings(self.request.tid,
                                     self.current_user.user_id,
                                     self.request.language)

    def put(self):
        """
        Parameters: None
        Request: ReceiverReceiverDesc
        Response: ReceiverReceiverDesc
        """
        request = self.validate_message(self.request.content.read(), requests.ReceiverReceiverDesc)

        return update_receiver_settings(self.request.tid,
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
        """
        Response: receiverTipList
        """
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
        """
        Request: ReceiverOperationDesc
        """
        request = self.validate_message(self.request.content.read(), requests.ReceiverOperationDesc)

        if request['operation'] not in ['postpone', 'delete']:
            raise errors.ForbiddenOperation

        return perform_tips_operation(self.request.tid,
                                      self.current_user.user_id,
                                      request['operation'],
                                      request['rtips'])
