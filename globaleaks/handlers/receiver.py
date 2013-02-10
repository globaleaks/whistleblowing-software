# -*- coding: UTF-8
#   receiver
#   ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers in the GlobaLeaks Node.

from cyclone.web import asynchronous
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from twisted.internet.defer import inlineCallbacks

from globaleaks.transactors.crudoperations import CrudOperations
from globaleaks.transactors.authoperations import AuthOperations
from globaleaks.rest.base import validateMessage
from globaleaks.rest import requests
from globaleaks.rest.errors import ReceiverGusNotFound, InvalidInputFormat,\
    ProfileGusNotFound, ReceiverConfNotFound, InvalidTipAuthToken, TipGusNotFound, ForbiddenOperation, ContextGusNotFound


class ReceiverInstance(BaseHandler):
    """
    R1
    This class permit the operations in the Receiver model options,
        Receiver.know_languages
        Receiver.name
        Receiver.tags
        Receiver.description

    and permit the overall view of all the Tips related to the receiver
    GET and PUT /receiver/(auth_secret_token)/management
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Response: receiverReceiverDesc
        Errors: TipGusNotFound, InvalidInputFormat, InvalidTipAuthToken
        """

        try:
            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().get_receiver_by_receiver(auth_user['receiver_gus'])

            self.write(answer['data'])
            self.set_status(answer['code'])

        except (TipGusNotFound) as error:
            self.write_error(error)

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Request: receiverReceiverDesc
        Response: receiverReceiverDesc
        Errors: ReceiverGusNotFound, InvalidInputFormat, InvalidTipAuthToken, TipGusNotFound
        """

        try:
            request = validateMessage(self.request.body, requests.receiverReceiverDesc)

            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().update_receiver_by_receiver(auth_user['receiver_gus'], request)

            self.write(answer['data'])
            self.set_status(answer['code'])

        except (InvalidInputFormat, ReceiverGusNotFound, InvalidTipAuthToken, TipGusNotFound) as error:
            self.write_error(error)

        self.finish()


class TipsCollection(BaseHandler):
    """
    R5
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips/<receiver_token_auth/tip
    """

    @asynchronous
    @inlineCallbacks
    def get(self, tip_auth_token, *uriargs):
        """
        Parameters: tip_auth_token
        Response: receiverTipList
        Errors: InvalidTipAuthToken
        """

        try:
            # validateParameter(tip_auth_token, requests.tipGUS)
            # TODO validate parameter tip format or raise InvalidInputFormat
            # auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)
            # TODO need to be update in Auth and an update in get_tip_list

            answer = yield CrudOperations().get_tip_list(tip_auth_token)

            self.set_status(answer['code'])
            self.write(answer['data'])

        except (TipGusNotFound) as error:
            self.write_error(error)

        self.finish()




