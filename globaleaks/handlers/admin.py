# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#

from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.transactors.crudoperations import CrudOperations

from globaleaks.utils import log
from globaleaks.plugins.manager import PluginManager
from globaleaks.rest.errors import ContextGusNotFound, ReceiverGusNotFound,\
    NodeNotFound, InvalidInputFormat, ProfileGusNotFound, ProfileNameConflict, ReceiverConfNotFound
from globaleaks.rest.base import validateMessage
from globaleaks.rest import requests


class NodeInstance(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    This would be likely see as the starting point of the administration chain:
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNodeDesc
        Errors: NodeNotFound
        """

        try:
            answer = yield CrudOperations().get_node()
            # validateMessage() output!!

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except NodeNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, *uriargs):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings
        """

        try:
            request = validateMessage(self.request.body, requests.adminNodeDesc)

            answer = yield CrudOperations().update_node(request)
            # validateMessage() output!!

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ContextsCollection(BaseHandler):
    """
    A2
    Return a list of all the available contexts, in elements
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminContextList
        Errors: None
        """

        try:
            answer = yield CrudOperations().get_context_list()

            # validateMessage() output!!

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """

        try:
            request = validateMessage(self.request.body, requests.adminContextDesc)
            answer = yield CrudOperations().create_context(request)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.json_write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

        self.finish()


class ContextInstance(BaseHandler):
    """
    A3
    classic CRUD in the single Context resource.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, context_gus, *uriargs):
        """
        Parameters: context_gus
        Response: adminContextDesc
        Errors: ContextGusNotFound, InvalidInputFormat
        """

        try:
            # validateParameter(context_gus, requests.contextGUS)
            answer = yield CrudOperations().get_context(context_gus)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ContextGusNotFound, ReceiverGusNotFound
        """

        try:
            # validateParameter(context_gus, requests.contextGUS)
            request = validateMessage(self.request.body, requests.adminContextDesc)

            answer = yield CrudOperations().update_context(context_gus, request)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.json_write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextGusNotFound
        """

        try:
            # validateParameter(context_gus, requests.contextGUS)
            answer = yield CrudOperations().delete_context(context_gus)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ReceiversCollection(BaseHandler):
    """
    A4
    List all available receivers present in the node.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminReceiverList
        Errors: None

        Admin operation: return all the receiver present in the Node
        """

        answer = yield CrudOperations().get_receiver_list()
        # validateMessage() output!!

        self.json_write(answer['data'])
        self.set_status(answer['code'])

        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ContextGusNotFound

        Create a new receiver
        """

        try:
            request = validateMessage(self.request.body, requests.adminReceiverDesc)

            answer = yield CrudOperations().create_receiver(request)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.json_write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

        self.finish()


class ReceiverInstance(BaseHandler):
    """
    A5
    AdminReceivers: classic CRUD in a 'receiver' resource
    A receiver can stay in more than one context, then is expected in POST/PUT
    operations a list of tarGET contexts is passed. Operation here, mostly are
    handled by models/receiver.py, and act on the administrative side of the
    receiver. a receiver performing operation in their profile, has an API
    implemented in handlers.receiver
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_gus, *uriargs):
        """
        Parameters: receiver_gus
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound

        Get an existent Receiver instance.
        """

        try:
            # validateParameter(receiver_gus, requests.receiverGUS)
            answer = yield CrudOperations().get_receiver(receiver_gus)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound, ContextGus

        Update information about a Receiver, return the instance updated.
        """

        try:
            # validateParameter(receiver_gus, requests.receiverGUS)
            request = validateMessage(self.request.body, requests.adminReceiverDesc)

            answer = yield CrudOperations().update_receiver(receiver_gus, request)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except KeyError, e: # Until validateMessage is not restored, it's needed.

            self.set_status(511)
            self.json_write({'error_message': "temporary error: %s" % e, 'error_code' : 123})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, receiver_gus, *uriargs):
        """
        Parameter: receiver_gus
        Request: None
        Response: None
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """

        try:
            # validateParameter(receiver_gus, requests.receiverGUS)
            answer = yield CrudOperations().delete_receiver(receiver_gus)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class PluginCollection(BaseHandler):
    """
    A6
    Return the list of all pluging (python file containing a self contained name, with an
    univoque name) available on the system.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminPluginList
        Errors: None

        This handler is one of the few that do not operate versus the database model, and
        then do not use CrudOperation, but works in the filesystem.
        Checks the plugin presents in the appropriate directory and return a list with
        name and properties.
        """

        plugin_descriptive_list = yield PluginManager.get_all()
        # TODO output validation - adminPluginList

        self.set_status(200)
        self.json_write(plugin_descriptive_list)
        self.finish()


class ProfileCollection(BaseHandler):
    """
    A7
    Return the list of all profiles configured based on the selected plugin name

    GET|POST /admin/plugin/<plugin_name>/profile
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: profile_gus
        Response: adminProfileList
        Errors: ProfileGusNotFound
        """

        answer = yield CrudOperations().get_profile_list()
        # validateMessage() output!!

        self.json_write(answer['data'])
        # TODO output validation - adminProfileList
        self.set_status(answer['code'])
        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminProfileDesc
        Response: adminProfileDesc
        Errors: InvalidInputFormat, ProfileNameConflict
        """

        try:
            # TODO input mesage validation, or InvalidInputFormat
            request = validateMessage(self.request.body, requests.adminProfileDesc)

            answer = yield CrudOperations().create_profile(request)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ProfileNameConflict, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class ProfileInstance(BaseHandler):
    """
    A8
    This class enable and configure the profiles, a profile is a plugin configuration,
    and the same plugin may have multiple profiles. This interface operate in a single
    requestd valid Profile (identified by a profile_gus)
    """

    @asynchronous
    @inlineCallbacks
    def get(self, profile_gus, *uriargs):
        """
        Parameters: profile_gus
        Response: adminProfileDesc
        Errors: ProfileGusNotFound
        """

        try:
            # validateParameter(profile_gus, requests.profileGUS)
            answer = yield CrudOperations().get_profile(profile_gus)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, profile_gus, *uriargs):
        """
        Parameters: profile_gus
        Request: adminProfileDesc
        Response: adminProfileDesc
        Errors: ProfileGusNotFound, InvalidInputFormat, ProfileNameConflict
        """

        try:
            # validateParameter(profile_gus, requests.profileGUS)
            request = validateMessage(self.request.body, requests.adminProfileDesc)

            answer = yield CrudOperations().update_profile(profile_gus, request)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ProfileNameConflict, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, profile_gus, *uriargs):
        """
        Request: adminProfileDesc
        Response: None
        Errors: ProfileGusNotFound, InvalidInputFormat
        """
        try:
            # validateParameter(profile_gus, requests.profileGUS)
            answer = yield CrudOperations().delete_profile(profile_gus)

            # validateMessage() output!!
            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class SettingsCollection(BaseHandler):
    """
    A9
    List of receiver configuration for admin management, based on a single receiver.
    Permit creation of a new receiver configuration, having a Receiver and a Profile ready.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, receiver_gus, *uriargs):
        """
        Parameters: receiver_gus
        Response: receiverConfList
        Errors: ReceiverGusNotFound
        """

        try:
            answer = yield CrudOperations().get_receiversetting_list(receiver_gus)

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, receiver_gus, *uriargs):
        """
        Parameters: receiver_gus
        Request: receiverConfDesc
        Response: receiverConfDesc
        Errors: ContextGusNotFound, ReceiverGusNotFound, InvalidInputFormat

        Create a new configuration for a plugin
        """

        try:
            request = validateMessage(self.request.body, requests.receiverConfDesc)
            # TODO validateParameter

            answer = yield CrudOperations().new_receiversetting(receiver_gus, request)

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class SettingsInstance(BaseHandler):
    """
    AA
    Admin interface management for CRUD over ReceiverSettings
    """

    @asynchronous
    @inlineCallbacks
    def get(self, conf_id, receiver_gus, *uriargs):
        """
        Parameters: receiver_gus, receiver_configuration_id
        Response: receiverConfDesc
        Errors: InvalidInputFormat, ReceiverConfNotFound, ReceiverGusNotFound
        """

        try:
            answer = yield CrudOperations().get_receiversetting(receiver_gus, conf_id)

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverConfNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def put(self, conf_id, receiver_gus, *uriargs):
        """
        Parameters: receiver_gus, receiver_configuration_id
        Response: receiverConfDesc
        Errors: InvalidInputFormat, ReceiverConfNotFound, ReceiverGusNotFound
        """

        try:
            request = validateMessage(self.request.body, requests.receiverReceiverDesc)

            answer = yield CrudOperations().update_receiversetting(receiver_gus, conf_id, request)

            self.json_write(answer['data'])
            self.set_status(answer['code'])

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ProfileGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, conf_id, receiver_gus, *uriargs):
        """
        Parameters: receiver_gus, receiver_configuration_id
        Response: receiverConfDesc
        Errors: InvalidInputFormat, ReceiverConfNotFound, ReceiverGusNotFound
        """

        try:
            # TODO validate parameters
            answer = yield CrudOperations().delete_receiversetting(receiver_gus, conf_id)

            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverConfNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


class StatisticsCollection(BaseHandler):
    """
    AB
    Return all administrative statistics of the node.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminStatsList
        Errors: None
        """
        pass

