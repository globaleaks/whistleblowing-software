# -*- coding: UTF-8
#   receiver
#   ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks

from globaleaks.utils import pretty_date_time, acquire_mail_address, log, acquire_bool
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import Receiver, ReceiverTip, ReceiverFile
from globaleaks.settings import transact
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import requests
from globaleaks.rest.errors import ReceiverGusNotFound, NoEmailSpecified, GPGKeyInvalid
from globaleaks.security import change_password, gpg_options_manage

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
        "gpg_key_remove": False,
        "gpg_key_armor": receiver.gpg_key_armor,
        "gpg_key_status": receiver.gpg_key_status,
        "gpg_enable_notification": receiver.gpg_enable_notification,
        "gpg_enable_files": receiver.gpg_enable_files,
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

    # receiver.notification_fields is not update until GLClient supports them
    receiver.tip_notification = acquire_bool(request['tip_notification'])
    receiver.comment_notification = acquire_bool(request['comment_notification'])
    receiver.file_notification = acquire_bool(request['file_notification'])

    gpg_options_manage(receiver, request)

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
        'creation_date' : unicode(pretty_date_time(rtip.creation_date)),
        'last_access' : unicode(pretty_date_time(rtip.last_access)),
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
