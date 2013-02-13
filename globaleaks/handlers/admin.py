# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
from datetime import datetime
now = datetime.utcnow

from cyclone.web import asynchronous
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated

from globaleaks.utils import log
from globaleaks.plugins.manager import PluginManager
from globaleaks.rest.errors import ContextGusNotFound, ReceiverGusNotFound,\
    NodeNotFound, InvalidInputFormat
from globaleaks.rest import requests

from globaleaks.models import Node

from globaleaks.settings import transact

def admin_serialize_node(node):
    node_dict = {'name': unicode(node.name),
      'description': unicode(node.description),
      'hidden_service': unicode(node.hidden_service),
      'public_site': unicode(node.public_site),
      'stats_update_time': int(node.stats_update_time),
      'email': unicode(node.email),
      'notification_settings': dict(node.notification_settings) if node.notification_settings else None,
      'password': unicode(node.password),
      'languages': list(node.languages)
    }
    return node_dict

def admin_serialize_context(context):
    context_dict = {
        "context_gus": context.id,
        "name": context.name,
        "description": context.description,
        "selectable_receiver": context.selectable_receiver,
        "languages": context.languages_supported if context.languages_supported else [],
        "tip_max_access": context.tip_max_access,
        "tip_timetolive": context.tip_timetolive,
        "file_max_download": context.file_max_download,
        "escalation_threshold": context.escalation_threshold,
        "fields": context.fields if context.fields else [],
        # This is to be set in the transaction
        "receivers": []
    }
    for receiver in context.receivers:
        context_dict['receivers'].append(receiver.id)

    return context_dict

def admin_serialize_receiver(receiver):
    response = {
        "receiver_gus": unicode(receiver.receiver_gus),
        "name": unicode(receiver.name),
        "description": unicode(receiver.description),
        "tags": list(receiver.tags) if receiver.tags else [],
        "languages": list(receiver.know_languages) if receiver.know_languages else [],
        "creation_date": unicode(gltime.prettyDateTime(receiver.creation_date)),
        "update_date": unicode(gltime.prettyDateTime(receiver.update_date)),
        "contexts": list(receiver.contexts) if receiver.contexts else [],
        "receiver_level": int(receiver.receiver_level),
        "can_delete_submission": bool(receiver.can_delete_submission),
        "can_postpone_expiration": bool(receiver.can_postpone_expiration),
        "can_configure_delivery": bool(receiver.can_configure_delivery),
        "can_configure_notification": bool(receiver.can_configure_notification),
        "username": unicode(receiver.username),
        "password": unicode(receiver.password),
        "notification_fields": dict(receiver.notification_fields)
    }
    return response

@transact
def get_node(store):
    """
    Returns:
        (dict) the currently configured node.
    """
    node = store.find(Node).one()
    return admin_serialize_node(node)

@transact
def update_node(store, node_gus, request):
    """
    Update the node, setting the last update time on it.

    Returns:
        the last update time of the node as a :class:`datetime.datetime`
        instance
    """
    node = store.find(Node, Node.id == unicode(node_gus)).one()
    last_update = node.last_update

    for key, value in request.items():
        setattr(node, key, value)
    node.last_update = now()

    return last_update

@transact
def get_context_list(store):
    """
    Returns:
        (dict) the current context list serialized.
    """
    contexts = store.find(Context)
    context_list = []

    for context in contexts:
        context_list.append(admin_serialize_context(context))

    return context_list

@transact
def create_context(store, request):
    """
    Creates a new context from the request of a client.

    We associate to the context the list of receivers and if the receiver is
    not valid we raise a ReceiverGusNotFound exception.

    Args:
        (dict) the request containing the keys to set on the model.

    Returns:
        (dict) representing the configured context
    """
    if 'receivers' in request:
        receivers = request['receivers']
        del request['receivers']

    receiver_list = []
    context = Context(request)
    store.add(context)

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        if not receiver:
            raise ReceiverGusNotFound
        context.receivers.add(receiver)

    return admin_serialize_context(context)

@transact
def get_context(store, context_gus):
    """
    Returns:
        (dict) the currently configured node.
    """
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
        raise ContextGusNotFound

    return admin_serialize_context(context)

@transact
def update_context(store, context_gus, request):
    """
    Updates the specified context. If the key receivers is specified we remove
    the current receivers of the Context and reset set it to the new specified
    ones.
    If no such context exists raises :class:`globaleaks.errors.ContextGusNotFound`.

    Args:
        context_gus:
            (unicode) the context_gus of the context to update

        request:
            (dict) the request to use to set the attributes of the Context

    Returns:
        last_update:
            (object) the last update time of the context.
    """
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
        raise ContextGusNotFound

    last_update = context.last_update
    receivers = request.get('receivers')
    if receivers:
        del request['receivers']

    for key, value in request.items():
        setattr(context, key, value)

    for receiver in context.receivers:
        context.remove(receiver)

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        context.receivers.add(receiver)
    context.last_update = now()

    return last_update

@transact
def delete_context(store, context_gus):
    """
    Deletes the specified context. If no such context exists raises
    :class:`globaleaks.errors.ContextGusNotFound`.

    Args:
        context_gus: the context gus of the context to remove.
    """
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
        raise ContextGusNotFound

    store.delete(context)
    return last_update

@transact
def get_receiver_list(store):
    """
    Returns:
        (list) the list of receivers
    """
    receiver_list = []

    receivers = store.find(Receiver)
    for receiver in receivers:
        receiver_list.append(admin_serialize_receiver(receiver))

    return receiver_list

@transact
def create_receiver(store, request):
    """
    Creates a new receiver.
    Returns:
        (dict) the configured receiver
    """
    receiver = Receiver(request)
    store.add(receiver)

    for context in receiver.contexts:
        context.receivers.add(receiver)

    return admin_serialize_receiver(receiver)

@transact
def get_receiver(store, receiver_gus):
    """
    raises :class:`globaleaks.errors.ReceiverGusNotFound` if the receiver does
    not exist.
    Returns:
        (dict) the receiver

    """
    receiver = store.find(Receiver, Receiver.id == unicode(receiver_gus)).one()

    if not receiver:
        raise ReceiverGusNotFound

    return admin_serialize_receiver(receiver)

@transact
def update_receiver(store, receiver_gus, request):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverGusNotFound` if the receiver does
    not exist.
    """
    receiver = store.find(Receiver, Receiver.id == receiver_gus)

    if not receiver:
        raise ReceiverGusNotFound

    last_update = receiver.last_update
    contexts = request.get('contexts')
    if contexts:
        del request['contexts']

    for key, value in request.items():
        setattr(receiver, key, value)

    for context in receiver.contexts:
        context.remove(receiver)

    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        receiver.contexts.add(context)

    context.last_update = now()
    return last_update

class NodeInstance(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    /node
    """
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNodeDesc
        Errors: NodeNotFound
        """
        response = yield get_node()
        self.finish(response)

    @inlineCallbacks
    def put(self, *uriargs):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings.
        """
        request = self.validate_message(self.request.body, requests.adminNodeDesc)

        last_update = yield update_node(request)
        response = yield get_node()
        response['last_update'] = last_update

        self.finish(response)

class ContextsCollection(BaseHandler):
    """
    A2
    Return a list of all the available contexts, in elements.

    /admin/context
    """
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminContextList
        Errors: None
        """
        response = yield get_context_list()

        self.set_status(200)
        self.finish(response)

    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """
        request = self.validate_message(self.request.body, requests.adminContextDesc)

        response = yield create_context(request)

        self.set_status(200)
        self.finish(response)

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
        response = yield get_context(context_gus)
        self.set_status(200)
        self.finish(response)

    @inlineCallbacks
    def put(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ContextGusNotFound, ReceiverGusNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.adminContextDesc)

        last_update = yield update_context(context_gus, request)
        response = yield get_context(context_gus)
        response['last_update'] = last_update

        self.set_status(200)
        self.finish(response)

    @inlineCallbacks
    def delete(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextGusNotFound
        """
        yield delete_context(context_gus)
        self.set_status(200)

class ReceiversCollection(BaseHandler):
    """
    A4
    List all available receivers present in the node.
    """

    @inlineCallbacks
    @authenticated('admin')
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminReceiverList
        Errors: None

        Admin operation: return all the receiver present in the Node
        """
        response = yield get_receiver_list()

        self.set_status(200)
        self.finish(response)

    @inlineCallbacks
    @authenticated('admin')
    def post(self, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ContextGusNotFound

        Create a new receiver
        """
        request = self.validate_message(self.request.body,
                requests.adminReceiverDesc)

        response = yield create_receiver(request)

        self.set_status(200)
        self.finish(response)

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
        response = yield get_receiver(receiver_gus)

        self.set_status(200)
        self.finish(response)

    @inlineCallbacks
    def put(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound, ContextGus

        Update information about a Receiver, return the instance updated.
        """
        request = self.validate_message(self.request.body, requests.adminReceiverDesc)

        last_update = yield update_receiver(receiver_gus, request)
        response = get_receiver(receiver_gus)

        self.set_status(200)
        self.finish(response)

    @inlineCallbacks
    def delete(self, receiver_gus, *uriargs):
        """
        Parameter: receiver_gus
        Request: None
        Response: None
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """
        yield delete_receiver(receiver_gus)

        self.set_status(200)
        self.finish()

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

