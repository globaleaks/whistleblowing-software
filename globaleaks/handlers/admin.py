# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
from datetime import datetime
from globaleaks.models import Node, Context
from globaleaks.settings import transact

now = datetime.utcnow

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated
from globaleaks.transactors.crudoperations import CrudOperations


from globaleaks.plugins.manager import PluginManager
from globaleaks.rest.errors import ContextGusNotFound, ReceiverGusNotFound,\
    NodeNotFound, InvalidInputFormat
from globaleaks.rest import requests


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

@transact
def get_node(store):
    node = store.find(Node).one()
    return admin_serialize_node(node)

@transact
def update_node(store, node_gus, request):
    node = store.find(Node, Node.id == unicode(node_gus)).one()
    last_update = node.last_update

    for key, value in request.items():
        setattr(node, key, value)
    node.last_update = now()

    return last_update

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
        answer = yield get_node()
        self.finish(answer)

    @inlineCallbacks
    def put(self, *uriargs):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings
        """
        request = self.validate_message(self.request.body, requests.adminNodeDesc)

        last_update = yield update_node(request)
        yield get_node()
        self.finish(answer)

@transact
def get_context_list(store):
    context_iface = Context(store)
    all_contexts = context_iface.get_all()

    self.returnData(all_contexts)
    self.returnCode(200)
    return self.prepareRetVals()

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

@transact
def get_context(store, context_gus):
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
        raise ContextGusNotFound

     context_dict = {
        "context_gus" : context.id,
        "name" : context.name,
        "description" : context.description,
        "selectable_receiver" : context.selectable_receiver,
        "languages" : context.languages_supported if context.languages_supported else [],
        'tip_max_access' : context.tip_max_access,
        'tip_timetolive' : context.tip_timetolive,
        'file_max_download' : context.file_max_download,
        'escalation_threshold' : context.escalation_threshold,
        'fields': context.fields if context.fields else [],
        'receivers' : context.receivers if context.receivers else []
    }
    return context_dict

@transact
def update_context(store, context_gus, request):
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    last_update = context.last_update

    receivers = request.get('receivers')
    del request['receivers']

    for key, value in request.items():
        setattr(context, key, value)

    for receiver in context.receivers:
        context.remove(receiver)

    for receiver_id in receivers:

        receiver = store.find(Receiver, Receiver.id == receiver_id).one()
        if not receiver:
            raise ReceiverGusNotFound

        context.receivers.add(receiver)

    context.last_update = now()

    return last_update

@transact
def delete_context(store, context_gus):
    context = store.find(Context, Context.id == unicode(context_gus)).one()
    store.delete(context)
    return last_update

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

def admin_serialize_receiver(receiver):
    response = {
        'receiver_gus': unicode(receiver.receiver_gus),
        'name': unicode(receiver.name),
        'description': unicode(receiver.description),
        'tags': list(receiver.tags) if receiver.tags else [],
        'languages': list(receiver.know_languages) if receiver.know_languages else [],
        'creation_date': unicode(gltime.prettyDateTime(receiver.creation_date)),
        'update_date': unicode(gltime.prettyDateTime(receiver.update_date)),
        'contexts': list(receiver.contexts) if receiver.contexts else [],
        'receiver_level': int(receiver.receiver_level),
        'can_delete_submission': bool(receiver.can_delete_submission),
        'can_postpone_expiration': bool(receiver.can_postpone_expiration),
        'can_configure_delivery': bool(receiver.can_configure_delivery),
        'can_configure_notification': bool(receiver.can_configure_notification),
        'username': unicode(receiver.username),
        'password': unicode(receiver.password),
        'notification_fields': dict(receiver.notification_fields)
    }
    return response

@transact
def get_receiver_list(store):
    receiver_list = []

    receivers = store.find(Receiver)
    for receiver in receivers:
        receiver_list.append(admin_serialize_receiver(receiver))

    return receiver_list

@transact
def create_receiver(store, request):
    receiver = Receiver(request)
    store.add(receiver)

    for context in receiver.contexts:
        context.receivers.add(receiver)

    return admin_serialize_receiver(receiver)

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
        answer = get_receiver_list()

        self.set_status(200)
        self.finish(answer)

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

        answer = yield create_receiver(request)

        self.set_status(200)
        self.finish(answer)

@transact
def get_receiver(store, receiver_gus):
    receiver = store.find(Receiver, Receiver.id == unicode(receiver_gus)).one()

    if not receiver:
        raise ReceiverGusNotFound

    return admin_serialize_receiver(receiver)

@transact
def update_receiver(store, receiver_gus, request):
    receiver = store.find(Receiver, Receiver.id == receiver_gus)

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
        answer = yield get_receiver(receiver_gus)

        self.set_status(200)
        self.finish(answer)

    @inlineCallbacks
    def put(self, receiver_gus, *uriargs):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound, ContextGus

        Update information about a Receiver, return the instance updated.
        """
        request = self.validate_message(self.request.body, requests.adminReceiverDesc)

        yield update_receiver(receiver_gus, request)
        answer = get_receiver(receiver_gus)

        self.set_status(200)
        self.finish(answer)


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

