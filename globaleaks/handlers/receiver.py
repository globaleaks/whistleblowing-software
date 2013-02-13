# -*- coding: UTF-8
#   receiver
#   ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers in the GlobaLeaks Node.

from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from twisted.internet.defer import inlineCallbacks

from globaleaks.models import Receiver, ReceiverTip
from globaleaks.settings import transact

from globaleaks.rest import requests
from globaleaks.rest.errors import ReceiverGusNotFound, InvalidInputFormat,\
    InvalidTipAuthToken, TipGusNotFound, ForbiddenOperation, ContextGusNotFound

# https://www.youtube.com/watch?v=BMxaLEGCVdg
def receiver_serialize_receiver(receiver):

    description = {
        "can_configure_delivery": receiver.can_configure_delivery,
        "can_configure_notification": receiver.can_configure_notification,
        "can_delete_submission": receiver.can_delete_submission,
        "can_postpone_expiration": receiver.can_postpone_expiration,
        "creation_date" : "XXX",
        "last_update" : "XXX",
        "description": receiver.description,
        "name": receiver.name,
        "notification_fields": dict(receiver.notification_fields),
        "id": receiver.id,
        # TODO REVIEW CLIENT CLONE XXX
        "receiver_gus": receiver.id,
        # XXX END TODO REMIND XXX
        "receiver_level": receiver.receiver_level,
        "username": receiver.username,
        "contexts": [],
    }

    for context in receiver.contexts:
        description['contexts'].append(context.id)

@transact
def get_receiver_settings(store, username):

    receiver = store.find(Receiver, Receiver.username == unicode(username)).one()

    if not receiver:
        raise ReceiverGusNotFound

    return receiver_serialize_receiver(receiver)

@transact
def update_receiver_settings(store, username, request):

    receiver = store.find(Receiver, Receiver.username == unicode(username)).one()

    if not receiver:
        raise ReceiverGusNotFound

    # TODO model_update with request

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
    GET and PUT /receiver/(auth_secret_token)/management
    """

    @inlineCallbacks
    def get(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Response: receiverReceiverDesc
        Errors: TipGusNotFound, InvalidInputFormat, InvalidTipAuthToken
        """
        # TODO align API and test after - now tip_id is ignored

        receiver_status = yield get_receiver_settings(self.current_user['username'])

        self.set_status(200)
        self.finish(receiver_status)


    @inlineCallbacks
    def put(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Request: receiverReceiverDesc
        Response: receiverReceiverDesc
        Errors: ReceiverGusNotFound, InvalidInputFormat, InvalidTipAuthToken, TipGusNotFound
        """
        # TODO align API and test after - now tip_id is ignored

        request = self.validate_message(self.request.body, requests.receiverReceiverDesc)

        receiver_status = yield update_receiver_settings(self.current_user['username'], request)

        self.set_status(200)
        self.finish(receiver_status)


@transact
def get_receiver_tip_list(store, username):



class TipsCollection(BaseHandler):
    """
    R5
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips/<receiver_token_auth/tip
    """

    @inlineCallbacks
    def get(self, tip_auth_token, *uriargs):
        """
        Parameters: tip_auth_token
        Response: receiverTipList
        Errors: InvalidTipAuthToken
        """

        answer = yield get_tip_list(self.current_user['username'])

        self.set_status(200)
        self.finish(answer)
