# -*- coding: UTF-8
# receiver
# ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks
from storm.expr import And, In

from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.user import db_user_update_user
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_postpone_expiration_date, db_delete_rtip
from globaleaks.handlers.submission import db_get_archived_preview_schema
from globaleaks.handlers.user import user_serialize_user
from globaleaks.models import Receiver, ReceiverTip
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.utils.utility import log, datetime_to_ISO8601

# https://www.youtube.com/watch?v=BMxaLEGCVdg
def receiver_serialize_receiver(receiver, language):
    ret_dict = user_serialize_user(receiver.user, language)

    ret_dict.update({
        'can_postpone_expiration': GLSettings.memory_copy.can_postpone_expiration or receiver.can_postpone_expiration,
        'can_delete_submission': GLSettings.memory_copy.can_delete_submission or receiver.can_delete_submission,
        'can_grant_permissions': GLSettings.memory_copy.can_grant_permissions or receiver.can_grant_permissions,
        'tip_notification': receiver.tip_notification,
        'ping_notification': receiver.ping_notification,
        'ping_mail_address': receiver.ping_mail_address,
        'tip_expiration_threshold': receiver.tip_expiration_threshold,
        'contexts': [c.id for c in receiver.contexts]
    })

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


@transact_ro
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

    ping_mail_address = request['ping_mail_address']
    if ping_mail_address != receiver.ping_mail_address:
        log.info("Ping email going to be updated, %s => %s" % (
            receiver.ping_mail_address, ping_mail_address))
        receiver.ping_mail_address = ping_mail_address

    receiver.tip_notification = request['tip_notification']
    receiver.ping_notification = request['ping_notification']

    return receiver_serialize_receiver(receiver, language)


@transact_ro
def get_receivertip_list(store, receiver_id, language):
    rtiplist = store.find(ReceiverTip, ReceiverTip.receiver_id == receiver_id)

    rtip_summary_list = []

    for rtip in rtiplist:
        mo = Rosetta(rtip.internaltip.context.localized_keys)
        mo.acquire_storm_object(rtip.internaltip.context)

        rtip_summary_list.append({
            'id': rtip.id,
            'creation_date': datetime_to_ISO8601(rtip.internaltip.creation_date),
            'last_access': datetime_to_ISO8601(rtip.last_access),
            'update_date': datetime_to_ISO8601(rtip.internaltip.update_date),
            'expiration_date': datetime_to_ISO8601(rtip.internaltip.expiration_date),
            'progressive': rtip.internaltip.progressive,
            'context_name': mo.dump_localized_key('name', language),
            'access_counter': rtip.access_counter,
            'file_counter': rtip.internaltip.internalfiles.count(),
            'comment_counter': rtip.internaltip.comments.count(),
            'message_counter': rtip.messages.count(),
            'tor2web': rtip.internaltip.tor2web,
            'questionnaire_hash': rtip.internaltip.questionnaire_hash,
            'preview_schema': db_get_archived_preview_schema(store, rtip.internaltip.questionnaire_hash, language),
            'preview': rtip.internaltip.preview,
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
        - timezone
        - password
        - notification settings
        - pgp key
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: ReceiverReceiverDesc
        Errors: ReceiverIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        receiver_status = yield get_receiver_settings(self.current_user.user_id,
                                                      self.request.language)

        self.set_status(200)
        self.finish(receiver_status)


    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def put(self):
        """
        Parameters: None
        Request: ReceiverReceiverDesc
        Response: ReceiverReceiverDesc
        Errors: ReceiverIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.body, requests.ReceiverReceiverDesc)

        receiver_status = yield update_receiver_settings(self.current_user.user_id,
                                                         request,
                                                         self.request.language)

        GLApiCache.invalidate('receivers')

        self.set_status(200)
        self.finish(receiver_status)


class TipsCollection(BaseHandler):
    """
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips
    """
    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self):
        """
        Response: receiverTipList
        Errors: InvalidAuthentication
        """
        answer = yield get_receivertip_list(self.current_user.user_id,
                                            self.request.language)

        self.set_status(200)
        self.finish(answer)


class TipsOperations(BaseHandler):
    """
    This interface receive some operation (postpone or delete) and a list of
    tips to apply.
    """
    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def put(self):
        """
        Parameters: ReceiverOperationDesc
        Res
        Errors: InvalidAuthentication, TipIdNotFound, ForbiddenOperation
        """
        request = self.validate_message(self.request.body, requests.ReceiverOperationDesc)

        if request['operation'] not in ['postpone', 'delete']:
            raise errors.ForbiddenOperation

        yield perform_tips_operation(self.current_user.user_id, request['operation'], request['rtips'])

        self.set_status(200)
        self.finish()
