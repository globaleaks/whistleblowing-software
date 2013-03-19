# -*- coding: UTF-8
#   receiver
#   ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers in the GlobaLeaks Node.

from globaleaks.utils import log
from globaleaks import utils
from globaleaks.handlers.base import BaseHandler
from twisted.internet.defer import inlineCallbacks

from globaleaks.models import Receiver, ReceiverTip
from globaleaks.settings import transact
from globaleaks.handlers.authentication import authenticated, transport_security_check

from globaleaks.rest import requests
from globaleaks.rest.errors import ReceiverGusNotFound, NoEmailSpecified, InvalidOldPassword

# https://www.youtube.com/watch?v=BMxaLEGCVdg
def receiver_serialize_receiver(receiver):
    description = {
        "receiver_gus": receiver.id,
        "name": receiver.name,
        "description": receiver.description,
        "update_date": utils.pretty_date_time(receiver.last_update),
        "creation_date": utils.pretty_date_time(receiver.creation_date),
        "receiver_level": receiver.receiver_level,
        "can_delete_submission": receiver.can_delete_submission,
        "username": receiver.username,
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

    if new_password and old_password:
        if receiver.password == old_password:
            receiver.password = new_password
        else:
            raise InvalidOldPassword
    elif new_password:
        raise InvalidOldPassword

    mail_address = utils.acquire_mail_address(request)
    if not mail_address:
        raise NoEmailSpecified

    receiver.notification_fields = request['notification_fields']

    return receiver_serialize_receiver(receiver)


class ReceiverInstance(BaseHandler):
    """
    R1
    This class permit the operations in the Receiver model options,
        Receiver.know_languages
        Receiver.name
        Receiver.tags
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
        Parameters: receiver_token_auth
        Response: receiverReceiverDesc
        Errors: TipGusNotFound, InvalidInputFormat, InvalidTipAuthToken
        """
        # TODO align API and test after - now tip_id is ignored

        receiver_status = yield get_receiver_settings(self.current_user['user_id'])

        self.set_status(200)
        self.finish(receiver_status)


    @inlineCallbacks
    @transport_security_check('receiver')
    @authenticated('receiver')
    def put(self):
        """
        Parameters: receiver_token_auth
        Request: receiverReceiverDesc
        Response: receiverReceiverDesc
        Errors: ReceiverGusNotFound, InvalidInputFormat, InvalidTipAuthToken, TipGusNotFound
        """
        # TODO align API and test after - now tip_id is ignored

        request = self.validate_message(self.request.body, requests.receiverReceiverDesc)

        receiver_status = yield update_receiver_settings(self.current_user['user_id'], request)

        self.set_status(200)
        self.finish(receiver_status)


def serialize_tip_summary(rtip):

    return {
        'access_counter': rtip.access_counter,
        'expressed_pertinence': rtip.expressed_pertinence,
        'creation_date' : unicode(utils.pretty_date_time(rtip.creation_date)),
        'last_acesss' : unicode(utils.pretty_date_time(rtip.last_access)),
        'id' : rtip.id
    }


@transact
def get_receiver_tip_list(store, user_id):

    receiver = store.find(Receiver, Receiver.id == unicode(user_id)).one()

    tiplist = store.find(ReceiverTip, ReceiverTip.receiver_id == receiver.id)

    tip_summary_list = []

    for tip in tiplist:
        tip_summary_list.append(serialize_tip_summary(tip))

    return tip_summary_list


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
