# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#

from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated
from globaleaks.transactors.crudoperations import CrudOperations

from globaleaks.utils import log
from globaleaks.plugins.manager import PluginManager
from globaleaks.rest.errors import ContextGusNotFound, ReceiverGusNotFound,\
    NodeNotFound, InvalidInputFormat
from globaleaks.rest import requests


class NodeInstance(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    This would be likely see as the starting point of the administration chain:
    """
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNodeDesc
        Errors: NodeNotFound
        """
        answer = yield CrudOperations().get_node()
        self.write(answer['data'])
        self.set_status(answer['code'])


    @inlineCallbacks
    def put(self, *uriargs):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings
        """

        request = self.validate_message(self.request.body, requests.adminNodeDesc)
        answer = yield CrudOperations().update_node(request)
        self.write(answer['data'])
        self.set_status(answer['code'])


class ContextsCollection(BaseHandler):
    """
    A2
    Return a list of all the available contexts, in elements
    """
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminContextList
        Errors: None
        """
        answer = yield CrudOperations().get_context_list()

        self.set_status(answer['code'])
        self.finish(answer['data'])

    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """
        request = self.validate_message(self.request.body, requests.adminContextDesc)
        answer = yield CrudOperations().create_context(request)

        self.set_status(answer['code'])
        self.finish(answer['data'])


class ContextInstance(BaseHandler):
    """
    A3
    classic CRUD in the single Context resource.
    """

    @inlineCallbacks
    def get(self, context_gus, *uriargs):
        """
        Parameters: context_gus
        Response: adminContextDesc
        Errors: ContextGusNotFound, InvalidInputFormat
        """
        # validateParameter(context_gus, requests.contextGUS)
        answer = yield CrudOperations().get_context(context_gus)

        self.write(answer['data'])
        self.set_status(answer['code'])

    @inlineCallbacks
    def put(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ContextGusNotFound, ReceiverGusNotFound
        """
        # validateParameter(context_gus, requests.contextGUS)
        request = self.validate_message(self.request.body, requests.adminContextDesc)

        answer = yield CrudOperations().update_context(context_gus, request)

        self.write(answer['data'])
        self.set_status(answer['code'])

    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextGusNotFound
        """
        # validateParameter(context_gus, requests.contextGUS)
        answer = yield CrudOperations().delete_context(context_gus)

        self.write(answer['data'])
        self.set_status(answer['code'])


class ReceiversCollection(BaseHandler):
    """
    A4
    List all available receivers present in the node.
    """

    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminReceiverList
        Errors: None

        Admin operation: return all the receiver present in the Node
        """

        answer = yield CrudOperations().get_receiver_list()

        self.write(answer['data'])
        self.set_status(answer['code'])

    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ContextGusNotFound

        Create a new receiver
        """
        request = self.validate_message(self.request.body,
                requests.adminReceiverDesc)

        answer = yield CrudOperations().create_receiver(request)

        self.write(answer['data'])
        self.set_status(answer['code'])


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

    @inlineCallbacks
    def get(self, receiver_gus, *uriargs):
        """
        Parameters: receiver_gus
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound

        Get an existent Receiver instance.
        """
        # validateParameter(receiver_gus, requests.receiverGUS)
        answer = yield CrudOperations().get_receiver(receiver_gus)

        self.write(answer['data'])
        self.set_status(answer['code'])


    @inlineCallbacks
    def put(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound, ContextGus

        Update information about a Receiver, return the instance updated.
        """
        # validateParameter(receiver_gus, requests.receiverGUS)
        request = self.validate_message(self.request.body, requests.adminReceiverDesc)
        answer = yield CrudOperations().update_receiver(receiver_gus, request)
        # validateMessage() output!!
        self.write(answer['data'])
        self.set_status(answer['code'])


    @inlineCallbacks
    def delete(self, receiver_gus, *uriargs):
        """
        Parameter: receiver_gus
        Request: None
        Response: None
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """
        # validateParameter(receiver_gus, requests.receiverGUS)
        answer = yield CrudOperations().delete_receiver(receiver_gus)

        self.write(answer['data'])
        self.set_status(answer['code'])

class PluginCollection(BaseHandler):
    """
    A6
    Return the list of all pluging (python file containing a self contained name, with an
    univoque name) available on the system.
    """

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
        self.write(plugin_descriptive_list)


class StatisticsCollection(BaseHandler):
    """
    AB
    Return all administrative statistics of the node.
    """

    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminStatsList
        Errors: None
        """
        pass

