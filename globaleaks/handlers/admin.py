# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
from storm.exceptions import NotOneError
from globaleaks.settings import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated
from globaleaks.rest import errors, requests
from globaleaks.models import now, Receiver, Context, Node, Notification

from twisted.internet.defer import inlineCallbacks
from globaleaks import utils
from globaleaks.utils import log


def admin_serialize_node(node):
    response = {
      'name': node.name,
      'description': node.description,
      'hidden_service': node.hidden_service,
      'public_site': node.public_site,
      'stats_update_time': node.stats_update_time,
      'email': node.email,
      'languages': list(node.languages) if node.languages else []
    }
    return response

def admin_serialize_context(context):
    context_dict = {
        "context_gus": context.id,
        "name": context.name,
        "description": context.description,
        "selectable_receiver": context.selectable_receiver,
        "tip_max_access": context.tip_max_access,
        "tip_timetolive": context.tip_timetolive,
        "file_max_download": context.file_max_download,
        "escalation_threshold": context.escalation_threshold,
        "fields": context.fields if context.fields else [],
        "receivers": [],
    }
    for receiver in context.receivers:
        context_dict['receivers'].append(receiver.id)

    return context_dict

def admin_serialize_receiver(receiver):
    receiver_dict = {
        "receiver_gus": receiver.id,
        "name": receiver.name,
        "description": receiver.description,
        "update_date": utils.prettyDateTime(receiver.last_update),
        "receiver_level": receiver.receiver_level,
        "can_delete_submission": receiver.can_delete_submission,
        "username": receiver.username,
        "password": receiver.password,
        "notification_fields": dict(receiver.notification_fields or {'mail_address': ''}),
        "failed_login": receiver.failed_login,
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

    URLs:
        If one url is present, is properly validated

    Returns:
        the last update time of the node as a :class:`datetime.datetime`
        instance
    """
    node = store.find(Node).one()

    if len(request['old_password']) and len(request['password']):
        if node.password == request['old_password']:
            log.info("Administrator password update %s => %s" % (request['old_password'], request['password'] ))
            node.password = request['password']
        else:
            log.info("Password invalid! cannot be changed now")
            raise errors.InvalidOldPassword


    if len(request['public_site']) > 1:
        if not utils.acquire_url_address(request['public_site'], hidden_service=True, http=True):
            log.err("Invalid public page regexp in [%s]" % request['public_site'])
            raise errors.InvalidInputFormat("Invalid public site")

    if len(request['hidden_service']) > 1:
        if not utils.acquire_url_address(request['hidden_service'], hidden_service=True, http=False):
            log.err("Invalid hidden service regexp in [%s]" % request['hidden_service'])
            raise errors.InvalidInputFormat("Invalid hidden service")

    # name, description and integer value are acquired here
    node.update(request)

    node_desc = admin_serialize_node(node)
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
    receivers = request.get('receivers', [])
    context = Context(request)

    if not request['fields']:
        # When a new context is create, assign some spare fields
        context.fields = [
            {u'hint': u"Hint, I'm required", u'label': u'headline',
             u'name': u'headline', u'presentation_order': 1,
             u'required': True, u'type': u'text', u'value': u'' },
            {u'hint': u'The name of the Sun', u'label': u'Sun',
              u'name': u'Sun', u'presentation_order': 2,
              u'required': True, u'type': u'text',
              u'value': u"I'm the sun, I've not name"},
        ]
    else:
        context.fields = request['fields']

    if len(request['name']) < 1:
        raise errors.InvalidInputFormat("Context name is missing (1 char required)")

    if context.escalation_threshold and context.selectable_receiver:
        raise errors.ContextParameterConflict

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            raise errors.ReceiverGusNotFound
        context.receivers.add(receiver)

    store.add(context)
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

    receivers = request.get('receivers', [])

    context.fields = request['fields']

    for receiver in context.receivers:
        context.receivers.remove(receiver)

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            raise errors.ReceiverGusNotFound
        context.receivers.add(receiver)

    context.update(request)

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

    store.remove(context)

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

    mail_address = utils.acquire_mail_address(request)
    if not mail_address:
        raise errors.NoEmailSpecified

    # Pretend that username is unique:
    try:
        clone = store.find(Receiver, Receiver.username == mail_address).one()
    except NotOneError, e:
        log.err("Fatal: more than one receiver present with the requested username: %s" % mail_address)
        raise errors.InvalidInputFormat("already duplicated receiver username [%s]" % mail_address)

    if clone:
        log.err("Fatal: already present receiver with the requested username: %s" % mail_address)
        raise errors.InvalidInputFormat("already present receiver username [%s]" % mail_address)

    receiver = Receiver(request)

    receiver.username = mail_address
    receiver.notification_fields = request['notification_fields']
    receiver.failed_login = 0

    # XXX generate randomly and then mail to the user, mark receiver
    # as 'inactive' until password is changed by activation link
    if not request['password'] or len(request['password']) == 0:
        receiver.password = u"globaleaks"
    else:
        receiver.password = request['password']

    store.add(receiver)

    contexts = request.get('contexts', [])
    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        if not context:
            raise errors.ContextGusNotFound
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

    mail_address = utils.acquire_mail_address(request)
    if not mail_address:
        raise errors.NoEmailSpecified

    receiver.username = mail_address
    receiver.notification_fields = request['notification_fields']
    receiver.password = request['password']

    contexts = request.get('contexts', [])

    for context in receiver.contexts:
        receiver.contexts.remove(context)

    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        if not context:
            raise errors.ContextGusNotFound
        receiver.contexts.add(context)

    receiver.update(request)

    receiver_desc = admin_serialize_receiver(receiver)
    receiver.last_update = now()
    return receiver_desc

@transact
def delete_receiver(store, id):

    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        raise errors.ReceiverGusNotFound

    store.remove(receiver)


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
    @inlineCallbacks
    @authenticated('admin')
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNodeDesc
        Errors: NodeNotFound
        """
        node_description = yield get_node()
        self.set_status(200)
        self.finish(node_description)

    @inlineCallbacks
    @authenticated('admin')
    def put(self, *uriargs):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings.
        """
        request = self.validate_message(self.request.body,
                requests.adminNodeDesc)

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
    @authenticated('admin')
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
    @authenticated('admin')
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
    @authenticated('admin')
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
    @authenticated('admin')
    def put(self, context_gus, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ContextGusNotFound, ReceiverGusNotFound
        """

        request = self.validate_message(self.request.body,
                                        requests.adminContextDesc)

        response = yield update_context(context_gus, request)

        self.set_status(202) # Updated
        self.finish(response)

    @inlineCallbacks
    @authenticated('admin')
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
    @authenticated('admin')
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
    @authenticated('admin')
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
    @authenticated('admin')
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



# Notification section:

def admin_serialize_notification(notif):
    notification_dict = {
        'server': notif.server if notif.server else u"",
        'port': notif.port if notif.port else u"",
        'username': notif.username if notif.username else u"",
        'password': notif.password if notif.password else u"",
        'security': notif.security if notif.security else u"",
        'tip_template': notif.tip_template if notif.tip_template else u"",
        'file_template': notif.file_template if notif.file_template else u"",
        'comment_template': notif.comment_template if notif.comment_template else u"",
        'activation_template': notif.activation_template if notif.activation_template else u"",
    }
    return notification_dict

@transact
def get_notification(store):
    try:
        notif = store.find(Notification).one()
    except Exception, e:
        log.err("Database error or application error: %s", str(e))
        raise e

    return admin_serialize_notification(notif)

@transact
def update_notification(store, request):

    try:
        notif = store.find(Notification).one()
    except Exception, e:
        log.err("Database error or application error: %s", str(e))
        raise e

    # TODO support languages here
    # TODO expand model unicode_keys when client is aligned

    security = str(request.get('security', u'')).upper()
    if security in Notification._security_types:
        notif.security = security
    else:
        raise errors.InvalidInputFormat("Security selection not recognized")

    notif.update(request)
    return admin_serialize_notification(notif)


class NotificationInstance(BaseHandler):
    """
    A6

    Manage Notification settings (account details and template)
    """

    @inlineCallbacks
    @authenticated('admin')
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNotificationDesc
        Errors: None (return empty configuration, at worst)
        """
        notification_desc = yield get_notification()
        self.set_status(200)
        self.finish(notification_desc)

    @inlineCallbacks
    @authenticated('admin')
    def put(self, *uriargs):
        """
        Request: adminNotificationDesc
        Response: adminNotificationDesc
        Errors: InvalidInputFormat

        Changes the node notification settings.
        """

        request = self.validate_message(self.request.body,
            requests.adminNotificationDesc)

        response = yield update_notification(request)

        self.set_status(202) # Updated
        self.finish(response)



# Removed from the Admin API
# plugin_descriptive_list = yield PluginManager.get_all()

