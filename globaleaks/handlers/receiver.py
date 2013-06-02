# -*- coding: UTF-8
#   receiver
#   ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks

from globaleaks.utils import pretty_date_time, pretty_diff_now, acquire_mail_address, log
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import Receiver, ReceiverTip, ReceiverFile
from globaleaks.settings import transact
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import requests
from globaleaks.rest.errors import ReceiverGusNotFound, NoEmailSpecified, GPGKeyInvalid
from globaleaks.security import change_password, import_gpg_key, gpg_clean

# https://www.youtube.com/watch?v=BMxaLEGCVdg
def receiver_serialize_receiver(receiver):
    description = {
        "receiver_gus": receiver.id,
        "name": receiver.name,
        "description": receiver.description,
        "update_date": pretty_date_time(receiver.last_update),
        "creation_date": pretty_date_time(receiver.creation_date),
        "receiver_level": receiver.receiver_level,
        "can_delete_submission": receiver.can_delete_submission,
        "username": receiver.username,
        "gpg_key_info": receiver.gpg_key_info,
        "gpg_key_fingerprint": receiver.gpg_key_fingerprint,
        "gpg_key_remove": True if receiver.gpg_key_status == Receiver._gpg_types[0] else False,
        "tags": receiver.tags,
        "tip_notification" : receiver.tip_notification,
        "file_notification" : receiver.file_notification,
        "comment_notification" : receiver.comment_notification,
        "notification_fields": dict(receiver.notification_fields),
        "failed_login": receiver.failed_login,
        "contexts": []
    }

    for context in receiver.contexts:
        description['contexts'].append(context.id)

    return description

@transact
def get_receiver_settings(store, user_id):
    receiver = store.find(Receiver, Receiver.id== unicode(user_id)).one()

    if not receiver:
        raise ReceiverGusNotFound

    return receiver_serialize_receiver(receiver)

@transact
def update_receiver_settings(store, user_id, request):
    receiver = store.find(Receiver, Receiver.id == unicode(user_id)).one()

    if not receiver:
        raise ReceiverGusNotFound

    new_password = request.get('password')
    old_password = request.get('old_password')

    if len(new_password) and len(old_password):
        # may raise exception change_password itself
        receiver.password = change_password(receiver.password,
                                            old_password, new_password, receiver.username)

    mail_address = acquire_mail_address(request)
    if not mail_address:
        raise NoEmailSpecified

    # At the moment, a receiver can update their email address, but not the username.
    # but client at the moment do not support this update, and has never been tested.
    receiver.notification_fields = request['notification_fields']

    # GPG management, a Receiver can perform three action:
    # 1) Setup a GPG key from a No Gpg Key
    # 2) Update a new GPG over an old GPG key
    # 3) Disable the GPG key present on the system (and start to receive plain text notification)
    new_gpg_key = request.get('gpg_key_armor', None)
    remove_key = request.get('gpg_key_remove', False)

    if remove_key:
        log.debug("User %s request to remove GPG key (%s)" %
                  (receiver.username, receiver.gpg_key_fingerprint))

        # In all the cases below, the key is marked disabled as request
        receiver.gpg_key_status = Receiver._gpg_types[0] # Disabled
        receiver.gpg_key_info = receiver.gpg_key_armor = receiver.gpg_key_fingerprint = None

    if new_gpg_key:

        log.debug("Importing a new GPG key for user %s" % receiver.username)

        key_info, key_fingerprint = import_gpg_key(receiver.username, new_gpg_key)

        # This step just import the key and check if it's correct. but GLB do not rely
        # on gnupg official fingerprint.

        if not key_info or not key_fingerprint:
            raise GPGKeyInvalid
        log.debug("Importing process: %s" % receiver.gpg_key_info)

        receiver.gpg_key_info = key_info
        receiver.gpg_key_fingerprint = key_fingerprint
        receiver.gpg_key_status = Receiver._gpg_types[1] # Enabled
        receiver.gpg_key_armor = new_gpg_key

        gpg_clean()
    # End of GPG key management for receiver

    return receiver_serialize_receiver(receiver)


class ReceiverInstance(BaseHandler):
    """
    R1
    This class permit to the receiver to modify some of their fields:
        Receiver.description
        Receiver.password

    and permit the overall view of all the Tips related to the receiver
    GET and PUT /receiver/preferences
    """

    @inlineCallbacks
    @transport_security_check('receiver')
    @authenticated('receiver')
    def get(self):
        """
        Parameters: None
        Response: receiverReceiverDesc
        Errors: TipGusNotFound, InvalidInputFormat, InvalidTipAuthToken
        """

        receiver_status = yield get_receiver_settings(self.current_user['user_id'])

        self.set_status(200)
        self.finish(receiver_status)


    @inlineCallbacks
    @transport_security_check('receiver')
    @authenticated('receiver')
    def put(self):
        """
        Parameters: None
        Request: receiverReceiverDesc
        Response: receiverReceiverDesc
        Errors: ReceiverGusNotFound, InvalidInputFormat, InvalidTipAuthToken, TipGusNotFound
        """
        request = self.validate_message(self.request.body, requests.receiverReceiverDesc)

        receiver_status = yield update_receiver_settings(self.current_user['user_id'], request)

        self.set_status(200)
        self.finish(receiver_status)


def serialize_tip_summary(rtip, file_associated):

    return {
        'access_counter': rtip.access_counter,
        # XXX total sum or personal expression ?
        'expressed_pertinence': rtip.expressed_pertinence,
        'creation_date' : unicode(pretty_diff_now(rtip.creation_date)),
        'last_access' : unicode(pretty_diff_now(rtip.last_access)),
        'id' : rtip.id,
        'files_number': file_associated,
    }


@transact
def get_receiver_tip_list(store, user_id):

    receiver = store.find(Receiver, Receiver.id == unicode(user_id)).one()

    rtiplist = store.find(ReceiverTip, ReceiverTip.receiver_id == receiver.id)

    rtip_summary_list = []

    for rtip in rtiplist:

        rfiles_n = store.find(ReceiverFile,
            (ReceiverFile.internaltip_id == rtip.internaltip.id,
             ReceiverFile.receiver_id == user_id)).count()

        rtip_summary_list.append(serialize_tip_summary(rtip, rfiles_n))

    return rtip_summary_list


class TipsCollection(BaseHandler):
    """
    R5
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips/<receiver_token_auth/tip
    """

    @inlineCallbacks
    @transport_security_check('receiver')
    @authenticated('receiver')
    def get(self):
        """
        Parameters: tip_auth_token
        Response: receiverTipList
        Errors: InvalidTipAuthToken
        """

        answer = yield get_receiver_tip_list(self.current_user['user_id'])

        self.set_status(200)
        self.finish(answer)
