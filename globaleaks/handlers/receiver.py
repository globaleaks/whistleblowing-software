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
import json

from globaleaks.models import receiver
from globaleaks.models import options
from globaleaks.models import internaltip
from globaleaks.models import externaltip
from globaleaks.rest.errors import ReceiverGusNotFound, InvalidInputFormat,\
    ProfileGusNotFound, ReceiverConfNotFound, InvalidTipAuthToken, TipGusNotFound


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
        Parameters: None
        Response: receiverReceiverDesc
        Errors: ReceiverGusNotFound, InvalidInputFormat, InvalidTipAuthToken
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverManagement", "GET", receiver_token_auth,
            "NOT YET IMPLEMENTED -- need to return tip list and receiver option, status, stats")

        self.set_status(500)
        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, receiver_token_auth, *uriargs):
        """
        Request: receiverReceiverDesc
        Response: receiverReceiverDesc
        Errors: ReceiverGusNotFound, InvalidInputFormat, InvalidTipAuthToken
        """

        log.debug("[D] %s %s " % (__file__, __name__), "Class ReceiverManagement", "PUT", receiver_token_auth,
            "NOT YET IMPLEMENTED -- need to accept update in know_languages, name, description, tags")

        self.set_status(500)
        self.finish()


class ProfilesCollection(BaseHandler):
    """
    R2
    This class show the profiles configured by the Administrator available in a specific context
    GET /receiver/(auth_secret_token)/plugin
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, *uriargs):
        """
        Parameters: None
        Response: receiverProfileList
        Errors: None
        """
        pass


class ProfileInstance(BaseHandler):
    """
    R3
    This class handle the receiver plugins configuration settings, its a
    CRUD operation active over ReceiverConfs entries, and specially in those fields:
        ReceiverConfs.configured_fields
        ReceiverConfs.active

    CRUD /receiver/(auth_secret_token)/plugin/<plugin_gus>
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, plugin_gus, *uriargs):
        """
        Parameters: None
        Response: receiverProfileDesc
        Errors: InvalidInputFormat, ProfileGusNotFound, TipGusNotFound, InvalidTipAuthToken
        """

        # TODO define an auth method usable easily before every Receiver operations, and
        # TODO various auth system

        receivertip_iface = externaltip.ReceiverTip()

        try:
            tip_gus = receiver_token_auth # XXX - XXX
            receiver_d = yield receivertip_iface.get_receiver_by_tip(tip_gus)
            # It's an auth, need to be managed in other way for supports welcome token
        except TipGusNotFound, e:
            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})
            receiver_d = None

        if receiver_d:

            confs_iface = options.ReceiverConfs()

            receiver_confs = yield confs_iface.receiver_get_all(receiver_d['receiver_gus'])

            self.set_status(200)
            self.write(receiver_confs)

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, receiver_token_auth, plugin_gus, *uriargs):
        """
        Request: receiverProfileDesc
        Response: receiverProfileDesc
        Errors: InvalidInputFormat, ProfileGusNotFound
        """

        # we have to make various check in this handler:
        # tip validation (thru ReceiverTip)
        # profile validation (thru , fields validation

        request = json.loads(self.request.body)
        receivertip_iface = externaltip.ReceiverTip()
        plugin_manager = GLPluginManager()
        profile_iface = options.PluginProfiles()


        profile_d = plugin_code = receiver_d = None
        try:
            receiver_d = yield receivertip_iface.get_receiver_by_tip(tip_gus)

            plugin_code = plugin_manager.get_plugins(request['plugin_type']).get(['plugin_name'])

            profile_d = profile_iface.admin_get_single(profile_gus)

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError:

            self.set_status(406)
            self.write({'error_message': 'Invalid plugin requested', 'error_code' : 123 })

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        # also request message validation would raise exception, when completed
        if not request:

            self.set_status(400)
            self.write({'error_message': 'Missing request!', 'error_code' : 123})

        if receiver_d and plugin_code and profile_d:

            config_iface = options.ReceiverConfs()

            # XXX also GLPlugin would raise an exception ya, just, I've too much commits in the belly XXX
            if plugin_code.validate_receiver_opt(profile_d['admin_fields'], request['receiver_fields']):

                yield config_iface.newconf(receiver_d['receiver_gus'], profile_gus, request['receiver_fields'], request['active'])
                self.set_status(200)

            else:

                self.set_status(400)
                self.write({'error_message': 'Invalid receiver settings', 'error_code' : 123})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, receiver_token_auth, plugin_gus, *uriargs):
        """
        Request: receiverProfileDesc
        Response: receiverProfileDesc
        Errors: InvalidInputFormat, ProfileGusNotFound
        """

        # we have to make various check in this handler:
        # tip validation (thru ReceiverTip)
        # profile validation (thru , fields validation

        request = json.loads(self.request.body)
        receivertip_iface = externaltip.ReceiverTip()
        plugin_manager = GLPluginManager()
        profile_iface = options.PluginProfiles()

        profile_d = plugin_code = receiver_d = None
        try:
            receiver_d = yield receivertip_iface.get_receiver_by_tip(tip_gus)

            plugin_code = plugin_manager.get_plugins(request['plugin_type']).get(['plugin_name'])

            profile_d = profile_iface.admin_get_single(profile_gus)

        except externaltip.TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError:

            self.set_status(406)
            self.write({'error_message': 'Invalid plugin requested', 'error_code' : 123 })

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        # also request message validation would raise exception, when completed
        if not request:

            self.set_status(400)
            self.write({'error_message': 'Missing request!', 'error_code' : 123})

        if receiver_d and plugin_code and profile_d:

            config_iface = options.ReceiverConfs()

            # XXX also GLPlugin would raise an exception ya, just, I've too much commits in the belly XXX
            if plugin_code.validate_receiver_opt(profile_d['admin_fields'], request['receiver_fields']):

                yield config_iface.updateconf(conf_id, request['receiver_fields'], request['active'])
                self.set_status(200)

            else:

                self.set_status(400)
                self.write({'error_message': 'Invalid receiver settings', 'error_code' : 123})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, receiver_token_auth, plugin_gus, *uriargs):
        """
        Request: receiverProfileDesc
        Response: None
        Errors: InvalidInputFormat, ProfileGusNotFound
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class AdminPlugin -- NOT YET IMPLEMENTED -- ", "DELETE")


class TipsCollection(BaseHandler):
    """
    R4
    This interface return the summary list of the Tips available for the authenticated Receiver
    GET /tips/<receiver_token_auth/tip
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, *uriargs):
        """
        Parameters: None
        Response: receiverTipList
        Errors: InvalidTipAuthToken
        """
        pass

