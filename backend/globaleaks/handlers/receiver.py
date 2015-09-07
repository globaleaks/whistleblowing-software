# -*- coding: UTF-8
# receiver
# ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks
from storm.expr import And, In

from globaleaks.handlers.admin import pgp_options_parse
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.node import get_public_receiver_list, anon_serialize_node
from globaleaks.handlers.rtip import db_postpone_expiration_date, db_delete_rtip
from globaleaks.handlers.submission import db_get_archived_preview_schema
from globaleaks.models import Receiver, ReceiverTip, ReceiverFile, Message, Node
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import change_password
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now

# https://www.youtube.com/watch?v=BMxaLEGCVdg
def receiver_serialize_receiver(receiver, node, language):
    ret_dict = {
        'id': receiver.id,
        'name': receiver.name,
        'can_postpone_expiration': node.can_postpone_expiration or receiver.can_postpone_expiration,
        'can_delete_submission': node.can_delete_submission or receiver.can_delete_submission,
        'username': receiver.user.username,
        'pgp_key_info': receiver.pgp_key_info,
        'pgp_key_fingerprint': receiver.pgp_key_fingerprint,
        'pgp_key_remove': False,
        'pgp_key_public': receiver.pgp_key_public,
        'pgp_key_expiration': datetime_to_ISO8601(receiver.pgp_key_expiration),
        'pgp_key_status': receiver.pgp_key_status,
        'tip_notification': receiver.tip_notification,
        'ping_notification': receiver.ping_notification,
        'mail_address': receiver.user.mail_address,
        'ping_mail_address': receiver.ping_mail_address,
        'tip_expiration_threshold': receiver.tip_expiration_threshold,
        'contexts': [c.id for c in receiver.contexts],
        'password': u'',
        'old_password': u'',
        'language': receiver.user.language,
        'timezone': receiver.user.timezone
    }

    for context in receiver.contexts:
        ret_dict['contexts'].append(context.id)

    return get_localized_values(ret_dict, receiver, receiver.localized_strings, language)


def serialize_event(evnt):
    """
    At the moment is not important to extract relevant information from the event_description but
    in the future it would be a nice improvement to get for example the beginning of the comment,
    or the filename/filetype, etc)
    """
    ret_dict = {
        'id': evnt.id,
        'creation_date': datetime_to_ISO8601(evnt.creation_date),
        'title': evnt.title,
        'mail_sent': evnt.mail_sent,
        'tip_id': evnt.receivertip_id
    }

    return ret_dict


@transact_ro
def get_receiver_settings(store, receiver_id, language):
    receiver = store.find(Receiver, Receiver.id == receiver_id).one()

    if not receiver:
        raise errors.ReceiverIdNotFound

    node = store.find(Node).one()

    return receiver_serialize_receiver(receiver, node, language)


@transact
def update_receiver_settings(store, receiver_id, request, language):
    """
    TODO: remind that 'description' is imported, but is not permitted
        by UI to be modified right now.
    """
    receiver = store.find(Receiver, Receiver.id == receiver_id).one()
    receiver.description[language] = request['description']

    if not receiver:
        raise errors.ReceiverIdNotFound

    receiver.user.language = request.get('language', GLSettings.memory_copy.default_language)
    receiver.user.timezone = request.get('timezone', GLSettings.memory_copy.default_timezone)

    new_password = request['password']
    old_password = request['old_password']

    if len(new_password) and len(old_password):
        receiver.user.password = change_password(receiver.user.password,
                                                 old_password,
                                                 new_password,
                                                 receiver.user.salt)

        if receiver.user.password_change_needed:
            receiver.user.password_change_needed = False

        receiver.user.password_change_date = datetime_now()

    ping_mail_address = request['ping_mail_address']

    if ping_mail_address != receiver.ping_mail_address:
        log.info("Ping email going to be updated, %s => %s" % (
            receiver.ping_mail_address, ping_mail_address))
        receiver.ping_mail_address = ping_mail_address

    receiver.tip_notification = request['tip_notification']
    receiver.ping_notification = request['ping_notification']

    pgp_options_parse(receiver, request)

    node = store.find(Node).one()

    return receiver_serialize_receiver(receiver, node, language)


@transact_ro
def get_receivertip_list(store, receiver_id, language):
    rtiplist = store.find(ReceiverTip, ReceiverTip.receiver_id == receiver_id)

    rtip_summary_list = []

    for rtip in rtiplist:
        # TODO this store find in a potentially long loop is bad, is easier store in
        # InternalTip the file counter number...
        rfiles_n = store.find(ReceiverFile,
                              (ReceiverFile.internaltip_id == rtip.internaltip.id,
                               ReceiverFile.receiver_id == receiver_id)).count()

        message_counter = store.find(Message,
                                     Message.receivertip_id == rtip.id).count()
        single_tip_sum = dict({
            'id': rtip.id,
            'creation_date': datetime_to_ISO8601(rtip.internaltip.creation_date),
            'last_access': datetime_to_ISO8601(rtip.last_access),
            'expiration_date': datetime_to_ISO8601(rtip.internaltip.expiration_date),
            'access_counter': rtip.access_counter,
            'file_counter': rfiles_n,
            'comment_counter': rtip.internaltip.comments.count(),
            'message_counter': message_counter,
            'tor2web': rtip.internaltip.tor2web,
            'questionnaire_hash': rtip.internaltip.questionnaire_hash,
            'preview_schema': db_get_archived_preview_schema(store, rtip.internaltip.questionnaire_hash, language),
            'preview': rtip.internaltip.preview,
            'label': rtip.label,
        })

        mo = Rosetta(rtip.internaltip.context.localized_strings)
        mo.acquire_storm_object(rtip.internaltip.context)
        single_tip_sum["context_name"] = mo.dump_localized_key('name', language)

        rtip_summary_list.append(single_tip_sum)

    return rtip_summary_list


@transact
def perform_tips_operation(store, receiver_id, operation, rtips_ids):
    node = store.find(Node).one()

    receiver = store.find(Receiver, Receiver.id == receiver_id).one()

    rtips = store.find(ReceiverTip, And(ReceiverTip.receiver_id == receiver_id,
                                        In(ReceiverTip.id, (rtips_ids))))

    if operation == 'postpone':
        can_postpone_expiration = node.can_postpone_expiration or receiver.can_postpone_expiration
        if not can_postpone_expiration:
            raise errors.ForbiddenOperation

        for rtip in rtips:
            db_postpone_expiration_date(rtip)

    elif operation == 'delete':
        can_delete_submission =  node.can_delete_submission or receiver.can_delete_submission
        if not can_delete_submission:
            raise errors.ForbiddenOperation

        for rtip in rtips:
            db_delete_rtip(store, rtip)

    log.debug("Multiple %s of %d Tips completed" % (operation, len(rtips_ids)))


class ReceiverInstance(BaseHandler):
    """
    This class permit to the receiver to modify some of their fields:
        Receiver.description
        Receiver.password

    and permit the overall view of all the Tips related to the receiver
    GET and PUT /receiver/preferences
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: ReceiverReceiverDesc
        Errors: TipIdNotFound, InvalidInputFormat, InvalidAuthentication
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
        Errors: ReceiverIdNotFound, InvalidInputFormat, InvalidAuthentication, TipIdNotFound
        """
        request = self.validate_message(self.request.body, requests.ReceiverReceiverDesc)

        receiver_status = yield update_receiver_settings(self.current_user.user_id,
                                                         request, self.request.language)

        # get the updated list of receivers, and update the cache
        public_receivers_list = yield get_public_receiver_list(self.request.language)
        GLApiCache.invalidate('receivers')
        GLApiCache.set('receivers', self.request.language, public_receivers_list)

        self.set_status(200)
        self.finish(receiver_status)


class TipsCollection(BaseHandler):
    """
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips/<receiver_token_auth/tip
    """

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self):
        """
        Parameters: tip_auth_token
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
        Response: None
        Errors: InvalidAuthentication, TipIdNotFound, ForbiddenOperation
        """
        request = self.validate_message(self.request.body, requests.ReceiverOperationDesc)

        if request['operation'] not in ['postpone', 'delete']:
            raise errors.ForbiddenOperation

        yield perform_tips_operation(self.current_user.user_id, request['operation'], request['rtips'])

        self.set_status(200)
        self.finish()
