# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
from globaleaks.settings import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated
from globaleaks.plugins.manager import PluginManager
from globaleaks.rest import errors, requests
from globaleaks.rest import requests
from globaleaks.models import now, Receiver, Context

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous
from globaleaks.utils import gltime


def admin_serialize_node(node):

    return {
      'name': unicode(node.name),
      'description': unicode(node.description),
      'hidden_service': unicode(node.hidden_service),
      'public_site': unicode(node.public_site),
      'stats_update_time': int(node.stats_update_time),
      'email': unicode(node.email),
      'notification_settings': dict(node.notification_settings) or None,
      'languages': list(node.languages)
    }

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
        "receivers": []
    }
    for receiver in context.receivers:
        context_dict['receivers'].append(receiver.id)

    return context_dict

def admin_serialize_receiver(receiver):

    receiver_dict = {
        "receiver_gus": unicode(receiver.receiver_gus),
        "name": unicode(receiver.name),
        "description": unicode(receiver.description),
        "tags": list(receiver.tags) if receiver.tags else [],
        "languages": list(receiver.know_languages) if receiver.know_languages else [],
        "creation_date": unicode(gltime.prettyDateTime(receiver.creation_date)),
        "update_date": unicode(gltime.prettyDateTime(receiver.update_date)),
        "receiver_level": int(receiver.receiver_level),
        "can_delete_submission": bool(receiver.can_delete_submission),
        "can_postpone_expiration": bool(receiver.can_postpone_expiration),
        "can_configure_delivery": bool(receiver.can_configure_delivery),
        "can_configure_notification": bool(receiver.can_configure_notification),
        "username": unicode(receiver.username),
        "password": unicode(receiver.password),
        "notification_fields": dict(receiver.notification_fields),
        "contexts": []
    }

    for context in receiver.contexts:
        receiver_dict['contexts'].append(context.id)

    return receiver_dict


@transact
def get_node(store):

    node = store.find(Node).one()
    return admin_serialize_node(node)

@transact
def update_node(store, request):
    """
    Update the node, setting the last update time on it.

    Password:
        If old_password and password are present, password update is performed

    Returns:
        the last update time of the node as a :class:`datetime.datetime`
        instance
    """
    node = store.find(Node).one()

    if request['old_password'] and request['password']:
        if node.password == request['old_password']:
            node.password = request['password']

    del request['old_password']
    del request['password']

    update_model(node, request)

    node_desc = admin_serialize_node(node)
    node_desc.last_update = now()
    return node_desc


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

    context = Context(request)
    store.add(context)

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        if not receiver:
            raise errors.ReceiverGusNotFound
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
        raise errors.ContextGusNotFound

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
            (dict) the serialized object updated
    """
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
        raise errors.ContextGusNotFound

    receivers = request.get('receivers')
    del request['receivers']

    update_model(context, request)

    for receiver in context.receivers:
        context.remove(receiver)

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        context.receivers.add(receiver)

    context_desc = admin_serialize_context(context)
    context.last_update = now()
    return context_desc

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
        raise errors.ContextGusNotFound

    store.delete(context)

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
    contexts = request.get('contexts')
    del request['contexts']
    receiver = Receiver(request)
    store.add(receiver)

    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        if not context:
            raise ContextGusNotFound
        context.receivers.add(receiver)

    return admin_serialize_receiver(receiver)

@transact
def get_receiver(store, id):
    """
    raises :class:`globaleaks.errors.ReceiverGusNotFound` if the receiver does
    not exist.
    Returns:
        (dict) the receiver

    """
    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        raise errors.ReceiverGusNotFound

    return admin_serialize_receiver(receiver)

@transact
def update_receiver(store, id, request):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverGusNotFound` if the receiver does
    not exist.
    """
    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        raise errors.ReceiverGusNotFound

    contexts = request.get('contexts')
    del request['contexts']

    update_model(receiver, request)

    for context in receiver.contexts:
        context.remove(receiver)

    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        receiver.contexts.add(context)

    receiver_desc = admin_serialize_context(receiver)
    receiver.last_update = now()
    return receiver_desc

@transact
def delete_receiver(store, id):

    context = store.find(Context, Context.id == unicode(id)).one()

    if not context:
        raise errors.ContextGusNotFound

    store.delete(context)


# ---------------------------------
# Below starts the Cyclone handlers
# ---------------------------------


class NodeInstance(BaseHandler):
    """
    A1
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    /node
    """
    @asynchronous
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNodeDesc
        Errors: NodeNotFound
        """
        node_desciption = yield get_node()
        self.set_status(200)
        self.finish(node_desciption)

    @inlineCallbacks
    def put(self, *uriargs):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings.
        """
        request = self.validate_message(self.request.body, requests.adminNodeDesc)

        response = yield update_node(request)

        self.set_status(202) # Updated
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

        self.set_status(201) # Created
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

        response = yield get_context(context_gus)

        self.set_status(202) # Updated
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

        self.set_status(201) # Created
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

        response = yield update_receiver(receiver_gus, request)

        self.set_status(201)
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

        # This is not a transact, it's right
        plugin_descriptive_list = yield PluginManager.get_all()

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

