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

from globaleaks.models.receiver import Receiver
from globaleaks.models.options import ReceiverConfs, PluginProfiles
from globaleaks.models.context import Context
from globaleaks.models.externaltip import ReceiverTip
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
            # TODO authenticate Receiver using cookie or token_auth

            receivertip_iface = ReceiverTip()

            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)
            # receivers_map is a dict with these keys: 'others' : [$], 'actor': $, 'mapped' [ ]

            # TODO output filtering to receiver recipient
            self.write(receivers_map['actor'])
            self.set_status(200)

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

        receivertip_iface = ReceiverTip()

        try:
            request = validateMessage(self.request.body, requests.receiverReceiverDesc)

            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)
            # receivers_map is a dict with these keys: 'others' : [$], 'actor': $, 'mapped' [ ]

            self_receiver_gus = receivers_map['actor']['receiver_gus']

            receiver_iface = Receiver()
            receiver_desc = yield receiver_iface.self_update(self_receiver_gus, request)

            # context_iface = Context()
            # yield context_iface.update_languages() -- TODO review in update languages and tags

            self.write(receiver_desc)
            self.set_status(200)

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
            # TODO receiver_token_auth sanity and security check

            receivertip_iface = ReceiverTip()
            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)
            # receivers_map is a dict with these keys: 'others' : [$], 'actor': $, 'mapped' [ ]

            receiver_associated_contexts = receivers_map['actor']['contexts']

            profile_iface = PluginProfiles()
            profiles_list = yield profile_iface.get_profiles_by_contexts(receiver_associated_contexts)

            # TODO output filtering to receiver recipient
            # self.write(json.dumps(profiles_list))
            self.write({'a' : profiles_list})
            self.set_status(200)

        except TipGusNotFound, e: # InvalidTipAuthToken

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ConfCollection(BaseHandler):
    """
    R3

    Return the collection of the current Profile Configuration of a Receiver, supports
    the creation of a new Configuration, based on an available Profile for the receiver.

    acts on /receivers/<receiver_token_auth/profileconf
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_token_auth, *uriargs):
        """
        Parameters: receiver_token_auth
        Response: receiverConfList
        Errors: TipGusNotFound, InvalidTipAuthToken
        """

        receivertip_iface = ReceiverTip()

        try:
            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)

            user = receivers_map['actor']

            receivercfg_iface = ReceiverConfs()
            confs_created = yield receivercfg_iface.get_confs_by_receiver(user['receiver_gus'])

            self.write(json.dumps(confs_created))
            self.set_status(200)

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

        receivertip_iface = ReceiverTip()

        try:
            request = validateMessage(self.request.body, requests.receiverReceiverDesc)

            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)
            user = receivers_map['actor']

            # ++ sanity checks that can't be make by validateMessage or by model:
            profile_iface = PluginProfiles()
            profile_desc = yield profile_iface.get_single(request['profile_gus'])

            if profile_desc['plugin_type'] == u'notification' and user['can_configure_notification']:
                pass
            elif profile_desc['plugin_type'] == u'delivery' and user['can_configure_delivery']:
                pass
            else:
                raise ForbiddenOperation
            # -- end of the sanity checks

            receivercfg_iface = ReceiverConfs()
            config_desc = yield receivercfg_iface.new(user['receiver_gus'], request)

            if config_desc['active']:
                # keeping active only the last configuration requested
                yield receivercfg_iface.deactivate_all_but(config_desc['config_id'], config_desc['context_gus'],
                    user['receiver_gus'], config_desc['plugin_type'])

            self.write(config_desc)
            self.set_status(201) # Created

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
    def get(self, receiver_token_auth, rconf_id, *uriargs):
        """
        Parameters: receiver_token_auth, receiver_configuration_id
        Response: receiverConfDesc
        Errors: InvalidInputFormat, ProfileGusNotFound, TipGusNotFound, InvalidTipAuthToken
        """

        receivertip_iface = ReceiverTip()

        try:
            # TODO receiver_token_auth and rconf_id validation

            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)

            user = receivers_map['actor']

            receivercfg_iface = ReceiverConfs()
            conf_requested = yield receivercfg_iface.get_single(rconf_id)

            self.write(conf_requested)
            # TODO output filtering, creating a receiverConfDesc
            self.set_status(200)

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

        except ProfileGusNotFound, e:

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

        receivertip_iface = ReceiverTip()

        try:
            request = validateMessage(self.request.body, requests.receiverReceiverDesc)

            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)
            user = receivers_map['actor']

            # ++ sanity checks that can't be make by validateMessage or by model:
            profile_iface = PluginProfiles()
            profile_desc = yield profile_iface.get_single(request['profile_gus'])

            if profile_desc['plugin_type'] == u'notification' and user['can_configure_notification']:
                pass
            elif profile_desc['plugin_type'] == u'delivery' and user['can_configure_delivery']:
                pass
            else:
                raise ForbiddenOperation
            # -- end of the sanity checks

            receivercfg_iface = ReceiverConfs()
            config_update = yield receivercfg_iface.update(conf_id, user['receiver_gus'], request)

            if config_update['active']:
                # keeping active only the last configuration requested
                yield receivercfg_iface.deactivate_all_but(config_update['config_id'], config_update['context_gus'],
                    user['receiver_gus'], config_update['plugin_type'])

            self.write(config_update)
            self.set_status(200) # OK

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

        receivertip_iface = ReceiverTip()

        try:
            # TODO validate parameters or raise InvalidInputFormat

            receivers_map = yield receivertip_iface.get_receivers_by_tip(receiver_token_auth)
            user = receivers_map['actor']

            receivercfg_iface = ReceiverConfs()
            yield receivercfg_iface.delete(conf_id, user['receiver_gus'])

            self.set_status(200) # OK

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

        receivertip_iface = ReceiverTip()

        try:
            # TODO validate parameter tip format or raise InvalidInputFormat

            tips = yield receivertip_iface.get_tips_by_tip(tip_auth_token)
            # this function return a dict with: { 'othertips': [$rtip], 'request' : $rtip }

            tips['othertips'].append(tips['request'])

            self.write(tips['othergroup'])

            self.set_status(200) # OK

        except TipGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()




