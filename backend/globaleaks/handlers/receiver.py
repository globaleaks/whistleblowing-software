# -*- coding: UTF-8
#   receiver
#   ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.utils.utility import log, acquire_bool, datetime_to_ISO8601
from globaleaks.utils.structures import Rosetta, Fields
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import Receiver, Context, ReceiverTip, ReceiverFile, Message, Node
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import requests, errors
from globaleaks.security import change_password, gpg_options_parse


# https://www.youtube.com/watch?v=BMxaLEGCVdg
def receiver_serialize_receiver(receiver, language=GLSetting.memory_copy.default_language):
    receiver_dict = {
        "id": receiver.id,
        "name": receiver.name,
        "update_date": datetime_to_ISO8601(receiver.last_update),
        "creation_date": datetime_to_ISO8601(receiver.creation_date),
        "receiver_level": receiver.receiver_level,
        "can_delete_submission": receiver.can_delete_submission,
        "username": receiver.user.username,
        "gpg_key_info": receiver.gpg_key_info,
        "gpg_key_fingerprint": receiver.gpg_key_fingerprint,
        "gpg_key_remove": False,
        "gpg_key_armor": receiver.gpg_key_armor,
        "gpg_key_status": receiver.gpg_key_status,
        "gpg_enable_notification": receiver.gpg_enable_notification,
        "tags": receiver.tags,
        "tip_notification" : receiver.tip_notification,
        "file_notification" : receiver.file_notification,
        "comment_notification" : receiver.comment_notification,
        "message_notification" : receiver.message_notification,
        "mail_address": receiver.mail_address,
                    # list is needed because .values returns a generator
        "contexts": list(receiver.contexts.values(Context.id)),
        "password": u'',
        "old_password": u'',
    }

    mo = Rosetta()
    mo.acquire_storm_object(receiver)
    receiver_dict["description"] = mo.dump_translated('description', language)

    for context in receiver.contexts:
        receiver_dict['contexts'].append(context.id)

    return receiver_dict

@transact_ro
def get_receiver_settings(store, receiver_id, language=GLSetting.memory_copy.default_language):
    receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()

    if not receiver:
        raise errors.ReceiverIdNotFound

    return receiver_serialize_receiver(receiver, language)

@transact
def update_receiver_settings(store, receiver_id, request, language=GLSetting.memory_copy.default_language):
    receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
    receiver.description[language] = request['description']

    if not receiver:
        raise errors.ReceiverIdNotFound

    new_password = request['password']
    old_password = request['old_password']

    if len(new_password) and len(old_password):
        receiver.user.password = change_password(receiver.user.password,
                                                 old_password,
                                                 new_password,
                                                 receiver.user.salt)

        if receiver.user.state == 'password_change_needed':
            receiver.user.state = 'enabled'

    mail_address = request['mail_address']

    if mail_address != receiver.mail_address:
        log.info("Email change %s => %s" % (receiver.mail_address, mail_address))
        receiver.mail_address = mail_address

    receiver.tip_notification = acquire_bool(request['tip_notification'])
    receiver.message_notification = acquire_bool(request['message_notification'])
    receiver.comment_notification = acquire_bool(request['comment_notification'])
    receiver.file_notification = acquire_bool(request['file_notification'])

    gpg_options_parse(receiver, request)

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
        Response: receiverReceiverDesc
        Errors: TipIdNotFound, InvalidInputFormat, InvalidTipAuthToken
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
        Request: receiverReceiverDesc
        Response: receiverReceiverDesc
        Errors: ReceiverIdNotFound, InvalidInputFormat, InvalidTipAuthToken, TipIdNotFound
        """
        request = self.validate_message(self.request.body, requests.receiverReceiverDesc)

        receiver_status = yield update_receiver_settings(self.current_user.user_id,
            request, self.request.language)

        self.set_status(200)
        self.finish(receiver_status)


@transact_ro
def get_receiver_tip_list(store, receiver_id, language=GLSetting.memory_copy.default_language):

    rtiplist = store.find(ReceiverTip, ReceiverTip.receiver_id == receiver_id)
    rtiplist.order_by(Desc(ReceiverTip.creation_date))

    node = store.find(Node).one()

    rtip_summary_list = []

    for rtip in rtiplist:

        postpone_superpower = (node.postpone_superpower or
                               rtip.internaltip.context.postpone_superpower or
                               rtip.receiver.postpone_superpower)

        can_delete_submission = (node.can_delete_submission or
                                 rtip.internaltip.context.can_delete_submission or
                                 rtip.receiver.can_delete_submission)

        rfiles_n = store.find(ReceiverFile,
            (ReceiverFile.internaltip_id == rtip.internaltip.id,
             ReceiverFile.receiver_id == receiver_id)).count()

        your_messages = store.find(Message,
                                   Message.receivertip_id == rtip.id,
                                   Message.type == u'receiver').count()

        unread_messages = store.find(Message,
                                     Message.receivertip_id == rtip.id,
                                     Message.type == u'whistleblower',
                                     Message.visualized == False).count()

        read_messages = store.find(Message,
                                   Message.receivertip_id == rtip.id,
                                   Message.type == u'whistleblower',
                                   Message.visualized == True).count()

        single_tip_sum = dict({
            'id' : rtip.id,
            'expressed_pertinence': rtip.expressed_pertinence,
            'creation_date' : datetime_to_ISO8601(rtip.creation_date),
            'last_access' : datetime_to_ISO8601(rtip.last_access),
            'expiration_date' : datetime_to_ISO8601(rtip.internaltip.expiration_date),
            'access_counter': rtip.access_counter,
            'files_number': rfiles_n,
            'comments_number': rtip.internaltip.comments.count(),
            'unread_messages' : unread_messages,
            'read_messages' : read_messages,
            'your_messages' : your_messages,
            'postpone_superpower': postpone_superpower,
            'can_delete_submission': can_delete_submission,
        })

        mo = Rosetta()
        mo.acquire_storm_object(rtip.internaltip.context)
        single_tip_sum["context_name"] = mo.dump_translated('name', language)

        preview_data = []

        fo = Fields(rtip.internaltip.context.localized_fields, rtip.internaltip.context.unique_fields)
        for preview_key, preview_label in fo.get_preview_keys(language).iteritems():

            # preview in a format angular.js likes
            try:
                entry = dict({'label' : preview_label,
                              'text': rtip.internaltip.wb_fields[preview_key] })

            except KeyError as xxx:
                log.err("Legacy error: suppressed 'preview_keys' %s" % xxx.message )
                continue

            preview_data.append(entry)

        single_tip_sum.update({ 'preview' : preview_data })
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
        Errors: InvalidTipAuthToken
        """

        answer = yield get_receiver_tip_list(self.current_user.user_id, self.request.language)

        self.set_status(200)
        self.finish(answer)
