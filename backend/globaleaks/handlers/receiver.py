# -*- coding: UTF-8
# receiver
# ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from storm.expr import And, In, Count

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_postpone_expiration_date, db_delete_rtip
from globaleaks.handlers.submission import db_serialize_archived_preview_schema
from globaleaks.handlers.user import db_user_update_user
from globaleaks.handlers.user import user_serialize_user
from globaleaks.models import ArchivedSchema, Comment, Context, InternalFile, InternalTip, Message, Receiver, \
    ReceiverTip
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.utils.utility import log, datetime_to_ISO8601


def receiver_serialize_receiver(receiver, language):
    ret_dict = user_serialize_user(receiver.user, language)

    ret_dict.update({
        'can_postpone_expiration': GLSettings.memory_copy.can_postpone_expiration or receiver.can_postpone_expiration,
        'can_delete_submission': GLSettings.memory_copy.can_delete_submission or receiver.can_delete_submission,
        'can_grant_permissions': GLSettings.memory_copy.can_grant_permissions or receiver.can_grant_permissions,
        'tip_notification': receiver.tip_notification,
        'contexts': [c.id for c in receiver.contexts]
    })

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


@transact
def get_receiver_settings(store, receiver_id, language):
    receiver = store.find(Receiver, Receiver.id == receiver_id).one()

    if not receiver:
        raise errors.ReceiverIdNotFound

    return receiver_serialize_receiver(receiver, language)


@transact
def update_receiver_settings(store, receiver_id, request, language):
    user = db_user_update_user(store, receiver_id, request, language)
    if not user:
        raise errors.UserIdNotFound

    receiver = store.find(Receiver, Receiver.id == receiver_id).one()
    if not receiver:
        raise errors.ReceiverIdNotFound

    receiver.tip_notification = request['tip_notification']

    return receiver_serialize_receiver(receiver, language)


@transact
def get_receivertip_list(store, receiver_id, language):
    rtip_summary_list = []

    rtips = store.find(ReceiverTip, ReceiverTip.receiver_id == receiver_id)
    itips_ids = [rtip.internaltip_id for rtip in rtips]

    itips_by_id = {}
    contexts_by_id = {}
    aqs_by_itip = {}
    comments_by_itip = {}
    internalfiles_by_itip = {}
    messages_by_rtip = {}

    for itip, context, archivedschema in store.find((InternalTip, Context, ArchivedSchema),
                                                     In(InternalTip.id, itips_ids),
                                                     Context.id == InternalTip.context_id,
                                                     ArchivedSchema.hash == InternalTip.questionnaire_hash,
                                                     ArchivedSchema.type == u'preview'):
        itips_by_id[itip.id] = itip
        contexts_by_id[context.id] = context
        aqs_by_itip[itip.id] = archivedschema

    result = store.find((ReceiverTip.id, Count()),  ReceiverTip.receiver_id == receiver_id, ReceiverTip.id == Message.receivertip_id).group_by(ReceiverTip)
    for rtip_id, count in result:
        messages_by_rtip[rtip_id] = count

    result = store.find((InternalTip.id, Count()), In(InternalTip.id, itips_ids), InternalTip.id == Comment.internaltip_id).group_by(InternalTip)
    for itip_id, count in result:
        comments_by_itip[itip_id] = count

    result = store.find((InternalTip.id, Count()), In(InternalTip.id, itips_ids), InternalTip.id == InternalFile.internaltip_id).group_by(InternalTip)
    for itip_id, count in result:
        internalfiles_by_itip[itip_id] = count

    for rtip in rtips:
        internaltip = itips_by_id[rtip.internaltip_id]
        context = contexts_by_id[internaltip.context_id]
        archivedschema = aqs_by_itip[rtip.internaltip_id]
        mo = Rosetta(context.localized_keys)
        mo.acquire_storm_object(context)

        rtip_summary_list.append({
            'id': rtip.id,
            'creation_date': datetime_to_ISO8601(internaltip.creation_date),
            'last_access': datetime_to_ISO8601(rtip.last_access),
            'update_date': datetime_to_ISO8601(internaltip.update_date),
            'expiration_date': datetime_to_ISO8601(internaltip.expiration_date),
            'progressive': internaltip.progressive,
            'new': rtip.access_counter == 0 or rtip.last_access < internaltip.update_date,
            'context_name': mo.dump_localized_key('name', language),
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
def perform_tips_operation(store, receiver_id, operation, rtips_ids):
    receiver = store.find(Receiver, Receiver.id == receiver_id).one()

    rtips = store.find(ReceiverTip, And(ReceiverTip.receiver_id == receiver_id,
                                        In(ReceiverTip.id, rtips_ids)))

    if operation == 'postpone':
        can_postpone_expiration = GLSettings.memory_copy.can_postpone_expiration or receiver.can_postpone_expiration
        if not can_postpone_expiration:
            raise errors.ForbiddenOperation

        for rtip in rtips:
            db_postpone_expiration_date(rtip)

    elif operation == 'delete':
        can_delete_submission =  GLSettings.memory_copy.can_delete_submission or receiver.can_delete_submission
        if not can_delete_submission:
            raise errors.ForbiddenOperation

        for rtip in rtips:
            db_delete_rtip(store, rtip)

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
        Errors: ReceiverIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        return get_receiver_settings(self.current_user.user_id,
                                     self.request.language)

    def put(self):
        """
        Parameters: None
        Request: ReceiverReceiverDesc
        Response: ReceiverReceiverDesc
        Errors: ReceiverIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.content.read(), requests.ReceiverReceiverDesc)

        return update_receiver_settings(self.current_user.user_id,
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
        Errors: InvalidAuthentication
        """
        return get_receivertip_list(self.current_user.user_id,
                                    self.request.language)


class TipsOperations(BaseHandler):
    """
    This interface receive some operation (postpone or delete) and a list of
    tips to apply.
    """
    check_roles = 'receiver'

    def put(self):
        """
        Parameters: ReceiverOperationDesc
        Res
        Errors: InvalidAuthentication, TipIdNotFound, ForbiddenOperation
        """
        request = self.validate_message(self.request.content.read(), requests.ReceiverOperationDesc)

        if request['operation'] not in ['postpone', 'delete']:
            raise errors.ForbiddenOperation

        return perform_tips_operation(self.current_user.user_id, request['operation'], request['rtips'])
