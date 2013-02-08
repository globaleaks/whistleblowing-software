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

        except TipGusNotFound, e: # InvalidTipAuthToken

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

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

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidTipAuthToken, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ProfilesCollection(BaseHandler):
    """
    R2
    This class show the profiles configured by the Administrator available to the various
    context which a receiver is part of. Using the information presents in receiver_fields,
    the receiver can operated in ProfileInstance API, configuing its own profile for every
    context which is part of.

    GET /receiver/(auth_secret_token)/profile
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Response: receiverProfileList
        Errors: None
        """

        try:
            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().get_profiles_by_receiver(auth_user['contexts'])

            self.write(answer['data'])
            self.set_status(answer['code'])

        except TipGusNotFound, e: # InvalidTipAuthToken

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ConfCollection(BaseHandler):
    """
    R3

    Return the collection of the current Profile Configuration of a Receiver, supports
    the creation of a new Configuration, based on an available Profile for the receiver.

    acts on /receivers/<receiver_token_auth>/profileconf
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Response: receiverConfList
        Errors: TipGusNotFound, InvalidTipAuthToken
        """

        try:
            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().get_receiversetting_list(auth_user['receiver_gus'])

            self.write(answer['data'])
            self.set_status(answer['code'])

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Request: receiverConfDesc
        Response: receiverConfDesc
        Errors: TipGusNotFound, InvalidTipAuthToken, ForbiddenOperation, ContextGusNotFound, ReceiverGusNotFound

        Create a new configuration for a plugin
        """

        try:
            request = validateMessage(self.request.body, requests.receiverConfDesc)

            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().new_receiversetting(auth_user['receiver_gus'], request, auth_user)

            self.write(answer['data'])
            self.set_status(answer['code'])

        except InvalidTipAuthToken, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ConfInstance(BaseHandler):
    """
    R4
    This class handle the receiver plugins configuration settings, its a
    CRUD operation active over ReceiverConfs entries, and specially in those fields:
        ReceiverConfs.configured_fields
        ReceiverConfs.active

    A receiver need to specify a ReceiverConfs for every context which is part of,
    If this operation seem to be redundant, can be wrapped client-side, just checking
    the Plugin name behind a Profile. Various Profile from the same Plugin, had in
    common the receiver_fields. Via client, can be easy wrap the setup of N profiles
    just asking to complete one time only the expected receiver_fields.

    CRUD /receiver/(auth_secret_token)/profileconf/<conf_id>
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, conf_id, *uriargs):
        """
        Parameters: receiver_token_auth, receiver_configuration_id
        Response: receiverConfDesc
        Errors: InvalidInputFormat, ProfileGusNotFound, TipGusNotFound, InvalidTipAuthToken
        """

        try:
            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().get_receiversetting(auth_user['receiver_gus'], conf_id)

            self.write(answer['data'])
            self.set_status(answer['code'])

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverConfNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidTipAuthToken, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, receiver_token_auth, conf_id, *uriargs):
        """
        Parameters:
        Parameters: receiver_token_auth, receiver_configuration_id
        Request: receiverConfDesc
        Response: receiverConfDesc
        Errors: InvalidInputFormat, ProfileGusNotFound, ContextGusNotFound, ReceiverGusNotFound,

        update the resource ReceiverConf by a specific receiver, and if is requested as active,
        deactivate the others related to the same context.
        """

        try:
            request = validateMessage(self.request.body, requests.receiverReceiverDesc)

            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().update_receiversetting(auth_user['receiver_gus'],
                conf_id, request, auth_user)

            self.write(answer['data'])
            self.set_status(answer['code'])

        except InvalidTipAuthToken, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, receiver_token_auth, conf_id, *uriargs):
        """
        Parameters: receiver_token_auth, receiver_configuration_id
        Request: receiverProfileDesc
        Response: None
        Errors: InvalidInputFormat, ProfileGusNotFound
        """

        try:
            auth_user = yield AuthOperations().authenticate_receiver(receiver_token_auth)

            answer = yield CrudOperations().delete_receiversetting(auth_user['receiver_gus'], conf_id)

            self.set_status(answer['code'])

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverConfNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

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

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()




