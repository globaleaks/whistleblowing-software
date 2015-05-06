# -*- coding: UTF-8
# receiver
# ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.handlers.admin import pgp_options_parse
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.node import get_public_receiver_list
from globaleaks.models import Receiver, ReceiverTip, ReceiverFile, Message, Node
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import change_password
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.utils.utility import log, acquire_bool, datetime_to_ISO8601, datetime_now

# https://www.youtube.com/watch?v=BMxaLEGCVdg
def receiver_serialize_receiver(receiver, language):
    ret_dict = {
        'id': receiver.id,
        'name': receiver.name,
        'update_date': datetime_to_ISO8601(receiver.last_update),
        'creation_date': datetime_to_ISO8601(receiver.creation_date),
        'can_delete_submission': receiver.can_delete_submission,
        'username': receiver.user.username,
        'pgp_key_info': receiver.pgp_key_info,
        'pgp_key_fingerprint': receiver.pgp_key_fingerprint,
        'pgp_key_remove': False,
        'pgp_key_public': receiver.pgp_key_public,
        'pgp_key_expiration': datetime_to_ISO8601(receiver.pgp_key_expiration),
        'pgp_key_status': receiver.pgp_key_status,
        'tip_notification': receiver.tip_notification,
        'ping_notification': receiver.ping_notification,
        'mail_address': receiver.mail_address,
        'ping_mail_address': receiver.ping_mail_address,
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

    return receiver_serialize_receiver(receiver, language)


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

    receiver.user.language = request.get('language', GLSetting.memory_copy.language)
    receiver.user.timezone = request.get('timezone', GLSetting.memory_copy.default_timezone)

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

    mail_address = request['mail_address']
    ping_mail_address = request['ping_mail_address']

    if mail_address != receiver.mail_address:
        log.err("Email cannot be change by receiver, only by admin " \
                "%s rejected. Kept %s" % (receiver.mail_address, mail_address))

    if ping_mail_address != receiver.ping_mail_address:
        log.info("Ping email going to be update, %s => %s" % (
            receiver.ping_mail_address, ping_mail_address))
        receiver.ping_mail_address = ping_mail_address

    receiver.tip_notification = acquire_bool(request['tip_notification'])

    pgp_options_parse(receiver, request)

    return receiver_serialize_receiver(receiver, language)


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


@transact_ro
def get_receivertip_list(store, receiver_id, language):
    rtiplist = store.find(ReceiverTip, ReceiverTip.receiver_id == receiver_id)
    rtiplist.order_by(Desc(ReceiverTip.creation_date))

    node = store.find(Node).one()

    rtip_summary_list = []

    for rtip in rtiplist:

        can_postpone_expiration = (node.can_postpone_expiration or
                                   rtip.internaltip.context.can_postpone_expiration or
                                   rtip.receiver.can_postpone_expiration)

        can_delete_submission = (node.can_delete_submission or
                                 rtip.internaltip.context.can_delete_submission or
                                 rtip.receiver.can_delete_submission)

        rfiles_n = store.find(ReceiverFile,
                              (ReceiverFile.internaltip_id == rtip.internaltip.id,
                               ReceiverFile.receiver_id == receiver_id)).count()

        message_counter = store.find(Message,
                                     Message.receivertip_id == rtip.id).count()

        single_tip_sum = dict({
            'id': rtip.id,
            'creation_date': datetime_to_ISO8601(rtip.creation_date),
            'last_access': datetime_to_ISO8601(rtip.last_access),
            'expiration_date': datetime_to_ISO8601(rtip.internaltip.expiration_date),
            'access_counter': rtip.access_counter,
            'file_counter': rfiles_n,
            'comment_counter': rtip.internaltip.comments.count(),
            'message_counter': message_counter,
            'can_postpone_expiration': can_postpone_expiration,
            'can_delete_submission': can_delete_submission,
        })

        mo = Rosetta(rtip.internaltip.context.localized_strings)
        mo.acquire_storm_object(rtip.internaltip.context)
        single_tip_sum["context_name"] = mo.dump_localized_attr('name', language)

        preview_data = []

        for s in rtip.internaltip.wb_steps:
            for f in s['children']:
                if f['preview']:
                    preview_data.append(f)

        single_tip_sum.update({'preview': preview_data})
        rtip_summary_list.append(single_tip_sum)

    return rtip_summary_list


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
