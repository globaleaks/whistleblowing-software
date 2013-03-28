# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
import os
from PIL import Image, ImageDraw
from random import randint

from globaleaks.settings import transact, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import errors, requests
from globaleaks.models import Receiver, Context, Node, Notification

from twisted.internet.defer import inlineCallbacks
from globaleaks import utils, security
from globaleaks.utils import log


def admin_serialize_node(node):
    response = {
      'name': node.name,
      'description': node.description,
      'hidden_service': node.hidden_service,
      'public_site': node.public_site,
      'stats_update_time': node.stats_update_time,
      'email': node.email,
      "last_update": utils.pretty_date_time(node.last_update),
      'languages': list(node.languages) if node.languages else []
    }
    return response

def admin_serialize_context(context):
    context_dict = {
        "context_gus": context.id,
        "name": context.name,
        "description": context.description,
        "creation_date": utils.pretty_date_time(context.creation_date),
        "last_update": utils.pretty_date_time(context.last_update),
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
        "creation_date": utils.pretty_date_time(receiver.creation_date),
        "last_update": utils.pretty_date_time(receiver.last_update),
        "receiver_level": receiver.receiver_level,
        "can_delete_submission": receiver.can_delete_submission,
        "username": receiver.username,
        "notification_fields": dict(receiver.notification_fields or {'mail_address': ''}),
        "failed_login": receiver.failed_login,
        "password": u"",
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
        node.password = security.change_password(node.password,
                                    request['old_password'], request['password'], node.salt)
        log.info("Administrator password update %s => %s" %
                 (request['old_password'], request['password'] ))

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
    node.last_update = utils.datetime_now()
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
            {u'hint': u"Describe your tip-off with a line/title", u'label': u'headline',
             u'name': u'headline', u'presentation_order': 1,
             u'required': True, u'type': u'text', u'value': u'' },
            {u'hint': u'Describe the details of your tip-off', u'label': u'Description',
              u'name': u'description', u'presentation_order': 2,
              u'required': True, u'type': u'text',
              u'value': u"" },
        ]
    else:
        context.fields = request['fields']

    if len(request['name']) < 1:
        log.err("Invalid request: name is an empty string")
        raise errors.InvalidInputFormat("Context name is missing (1 char required)")

    # Check that do not exists a Context with the proposed new name
    homonymous = store.find(Context, Context.name == unicode(request['name'])).count()
    if homonymous:
        log.err("Creation error: already present context with the specified name: %s"
                % request['name'])
        raise errors.ExpectedUniqueField('name', request['name'])

    if context.escalation_threshold and context.selectable_receiver:
        log.err("Parameter conflict in context creation")
        raise errors.ContextParameterConflict

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            log.err("Creation error: unexistent context can't be associated")
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
        log.err("Requested invalid context")
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

    # Check that do not exists already a Context with the proposed name
    homonymous = store.find(Context,
        ( Context.name == unicode(request['name']), Context.id != unicode(context_gus)) ).count()
    if homonymous:
        log.err("Update error: already present context with the specified name: %s" %
                request['name'])
        raise errors.ExpectedUniqueField('name', request['name'])

    for receiver in context.receivers:
        context.receivers.remove(receiver)

    receivers = request.get('receivers', [])
    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            log.err("Update error: unexistent receiver can't be associated")
            raise errors.ReceiverGusNotFound
        context.receivers.add(receiver)

    context.update(request)
    context.fields = request['fields']

    context_desc = admin_serialize_context(context)
    context.last_update = utils.datetime_now()
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
        log.err("Invalid context requested in removal")
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


def create_random_receiver_portrait(receiver_uuid):
    """
    Create a simple random gradient image, useful to recognize
    different Receivers by eye, until they do not change a portrait
    """
    img = Image.new("RGB", (300,300), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    r,g,b = randint(0,255), randint(0,255), randint(0,255)
    dr = (randint(0,255) - r)/300.
    dg = (randint(0,255) - g)/300.
    db = (randint(0,255) - b)/300.
    for i in range(300):
        r,g,b = r+dr, g+dg, b+db
        draw.line((i,0,i,300), fill=(int(r),int(g),int(b)))

    img.thumbnail((120, 120), Image.ANTIALIAS)
    img.save(os.path.join(GLSetting.static_path, "%s_120.png" % receiver_uuid),"PNG")
    img.thumbnail((40, 40), Image.ANTIALIAS)
    img.save(os.path.join(GLSetting.static_path, "%s_40.png" % receiver_uuid),"PNG")
    # perhaps think that we do not want OS operations during a receiver creation operations ?


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
    homonymous = store.find(Receiver, Receiver.username == mail_address).count()
    if homonymous:
        log.err("Creation error: already present receiver with the requested username: %s" % mail_address)
        raise errors.ExpectedUniqueField('mail_address', mail_address)

    receiver = Receiver(request)

    receiver.username = mail_address
    receiver.notification_fields = request['notification_fields']
    receiver.failed_login = 0

    # A password strength checker need to be implemented in the client, but here a
    # minimal check is put
    if not len(request['password']) >= security.MINIMUM_PASSWORD_LENGTH:
        log.err("Password of almost %d byte needed " % security.MINIMUM_PASSWORD_LENGTH)
        raise errors.InvalidInputFormat("Password of almost %d byte needed " %
                                        security.MINIMUM_PASSWORD_LENGTH)
    receiver.password = security.hash_password(request['password'], mail_address)

    store.add(receiver)
    create_random_receiver_portrait(receiver.id)

    contexts = request.get('contexts', [])
    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        if not context:
            log.err("Creation error: unexistent receiver can't be associated")
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
        log.err("Requested invalid receiver")
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

    homonymous = store.find(Receiver,
        ( Receiver.username == mail_address, Receiver.id != unicode(id)) ).count()
    if homonymous:
        log.err("Update error: already present receiver with the requested username: %s" % mail_address)
        raise errors.ExpectedUniqueField('mail_address', mail_address)

    receiver.username = mail_address
    receiver.notification_fields = request['notification_fields']

    if len(request['password']):
        # admin override password without effort :)
        receiver.password = security.hash_password(request['password'], mail_address)

    contexts = request.get('contexts', [])

    for context in receiver.contexts:
        receiver.contexts.remove(context)

    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        if not context:
            log.err("Update error: unexistent context can't be associated")
            raise errors.ContextGusNotFound
        receiver.contexts.add(context)

    receiver.update(request)

    receiver_desc = admin_serialize_receiver(receiver)
    receiver.last_update = utils.datetime_now()
    return receiver_desc

@transact
def delete_receiver(store, id):

    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        log.err("Invalid receiver requested in removal")
        raise errors.ReceiverGusNotFound

    portrait_120 = os.path.join(GLSetting.static_path, "%s_120.png" % id)
    portrait_40 = os.path.join(GLSetting.static_path, "%s_40.png" % id)

    if os.path.exists(portrait_120):
        os.unlink(portrait_120)

    if os.path.exists(portrait_40):
        os.unlink(portrait_40)

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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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
        log.err("Invalid request: Security option not recognized")
        raise errors.InvalidInputFormat("Security selection not recognized")

    notif.update(request)
    return admin_serialize_notification(notif)


class NotificationInstance(BaseHandler):
    """
    A6

    Manage Notification settings (account details and template)
    """

    @inlineCallbacks
    @transport_security_check('admin')
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
    @transport_security_check('admin')
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

