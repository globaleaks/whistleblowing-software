# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
import os, shutil

from globaleaks.settings import transact, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import errors, requests
from globaleaks.models import Receiver, Context, Node, Notification

from twisted.internet.defer import inlineCallbacks
from globaleaks import utils, security, models
from globaleaks.utils import log, acquire_localized
from globaleaks.db import import_memory_variables
from globaleaks.security import gpg_options_manage
from globaleaks import LANGUAGES_SUPPORTED_CODES

def admin_serialize_node(node, language):
    response = {
        "name": node.name,
        "description": utils.optlang(node.description, language),
        "creation_date": utils.pretty_date_time(node.creation_date),
        "last_update": utils.pretty_date_time(node.last_update),
        "hidden_service": node.hidden_service,
        "public_site": node.public_site,
        "stats_update_time": node.stats_update_time,
        "email": node.email,
        "version": GLSetting.version_string,
        "languages_supported": node.languages_supported,
        "languages_enabled": node.languages_enabled,
        'maximum_filesize': node.maximum_filesize,
        'maximum_namesize': node.maximum_namesize,
        'maximum_descsize': node.maximum_descsize,
        'maximum_textsize': node.maximum_textsize,
        'exception_email': node.exception_email,
        'tor2web_admin': GLSetting.memory_copy.tor2web_admin,
        'tor2web_submission': GLSetting.memory_copy.tor2web_submission,
        'tor2web_tip': GLSetting.memory_copy.tor2web_tip,
        'tor2web_receiver': GLSetting.memory_copy.tor2web_receiver,
        'tor2web_unauth': GLSetting.memory_copy.tor2web_unauth,
    }
    return response

def admin_serialize_context(context, language):
    context_dict = {
        "context_gus": context.id,
        "name": utils.optlang(context.name, language),
        "description": utils.optlang(context.description, language),
        "creation_date": utils.pretty_date_time(context.creation_date),
        "last_update": utils.pretty_date_time(context.last_update),
        "selectable_receiver": context.selectable_receiver,
        "tip_max_access": context.tip_max_access,
        # tip expressed in day, submission in hours
        "tip_timetolive": context.tip_timetolive / (60 * 60 * 24),
        "submission_timetolive": context.submission_timetolive / (60 * 60),
        "file_max_download": context.file_max_download,
        "escalation_threshold": context.escalation_threshold,
        "fields": utils.optlang_fields(context.fields, language) if context.fields else [],
        "receivers": [],
        "receipt_regexp": context.receipt_regexp,
        "receipt_description": u'NYI', # context.receipt_description, # optlang
        "submission_introduction": u'NYI', # context.submission_introduction, # optlang
        "submission_disclaimer": u'NYI', # context.submission_disclaimer, # optlang
        "tags": context.tags if context.tags else u"",
        "file_required": context.file_required,
    }
    
    for receiver in context.receivers:
        context_dict['receivers'].append(receiver.id)

    return context_dict

def admin_serialize_receiver(receiver, language):
    receiver_dict = {
        "receiver_gus": receiver.id,
        "name": receiver.name,
        "description": utils.optlang(receiver.description, language),
        "creation_date": utils.pretty_date_time(receiver.creation_date),
        "last_update": utils.pretty_date_time(receiver.last_update),
        "receiver_level": receiver.receiver_level,
        "can_delete_submission": receiver.can_delete_submission,
        "username": receiver.username,
        "notification_fields": dict(receiver.notification_fields or {'mail_address': ''}),
        "failed_login": receiver.failed_login,
        "password": u"",
        "contexts": [],
        "tags": receiver.tags,
        "gpg_key_info": receiver.gpg_key_info,
        "gpg_key_armor": receiver.gpg_key_armor,
        "gpg_key_remove": False,
        "gpg_key_fingerprint": receiver.gpg_key_fingerprint,
        "gpg_key_status": receiver.gpg_key_status,
        "gpg_enable_notification": receiver.gpg_enable_notification,
        "gpg_enable_files": receiver.gpg_enable_files,
        "comment_notification": receiver.comment_notification,
        "tip_notification": receiver.tip_notification,
        "file_notification": receiver.file_notification,
    }
    for context in receiver.contexts:
        receiver_dict['contexts'].append(context.id)

    return receiver_dict


@transact
def get_node(store, language):
    return admin_serialize_node(store.find(Node).one(), language)

@transact
def update_node(store, request, language):
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

    if len(request['public_site']) > 1:
        if not utils.acquire_url_address(request['public_site'], hidden_service=True, http=True):
            log.err("Invalid public page regexp in [%s]" % request['public_site'])
            raise errors.InvalidInputFormat("Invalid public site")

    if len(request['hidden_service']) > 1:
        if not utils.acquire_url_address(request['hidden_service'], hidden_service=True, http=False):
            log.err("Invalid hidden service regexp in [%s]" % request['hidden_service'])
            raise errors.InvalidInputFormat("Invalid hidden service")

    # verify that the languages enabled are valid 'code' in the languages supported
    node.languages_enabled = []
    for lang_code in request['languages_enabled']:
        if lang_code in LANGUAGES_SUPPORTED_CODES:
            node.languages_enabled.append(lang_code)
        else:
            raise errors.InvalidInputFormat("Invalid lang code: %s" % lang_code)

    request['description'] = acquire_localized(request['description'], language,
        node.description[language] )

    # name, description tor2web boolean value are acquired here
    node.update(request)
    node.last_update = utils.datetime_now()

    return admin_serialize_node(node)

@transact
def get_context_list(store, language):
    """
    Returns:
        (dict) the current context list serialized.
    """
    contexts = store.find(Context)
    context_list = []

    for context in contexts:
        context_list.append(admin_serialize_context(context, language))

    return context_list


def fields_validation(fields_list):

    if not len(fields_list):
        raise errors.InvalidInputFormat("Missing fields list")

    # the required keys are already validated by validate_jmessage
    # with globaleaks/rest/base.py formFieldDict
    # here are validated the types and the internal format

    accepted_form_type = [ "text", "radio", "select", "multiple",
                           "checkboxes",  "textarea", "number",
                           "url", "phone", "email" ]

    for field_desc in fields_list:
        check_type = field_desc['type']
        if not check_type in accepted_form_type:
            raise errors.InvalidInputFormat("Fields validation deny '%s' in %s" %
                                            (check_type, field_desc['name']) )


@transact
def create_context(store, request, language):
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

    request['name'] = acquire_localized(request['description'], language )
    request['description'] = acquire_localized(request['description'], language )
    request['receipt_description'] = acquire_localized(request['description'], language )
    request['submission_introduction'] = acquire_localized(request['submission_introduction'], language)
    request['submission_disclaimer'] = acquire_localized(request['submission_disclaimer'], language)

    context = Context(request)

    if not request['fields']:
        # When a new context is create, assign default fields, if not supply
        assigned_fields = [
            {u'hint': { "en" : u"Describe your tip-off with a line/title" },
             u'name': { "en" : u'Short title' }, u'presentation_order': 1,
             u'key': u'Short title',
             u'required': True, u'type': u'text', u'value': u'' },
            {u'hint': { "en" : u'Describe the details of your tip-off'},
              u'key': u'Full description', u'presentation_order': 2,
              u'name': { "en" : u'Full description' },
              u'required': True, u'type': u'text',
              u'value': u"" },
            {u'hint': { "en" : u"Describe the submitted files" },
             u'name': { "en" : u'Files description' },
             u'key': u'Files description', u'presentation_order': 3,
             u'required': False, u'type': u'text', u'value': u'' },
        ]
    else:
        assigned_fields = request['fields']

    # may raise InvalidInputFormat if fields format do not fit
    fields_validation(assigned_fields)
    context.fields = assigned_fields

    # verify if the default is provided by GLC
    context.receipt_regexp = GLSetting.defaults.receipt_regexp

    context.tags = request['tags']

    # Integrity checks related on name (need to exists, need to be unique)
    # are performed only on the english language at the moment

    try:
        # XXX this is the only insertion that *NEED* a GL-Language header
        context_name = request['name'][language]
    except Exception as excep:
        raise errors.InvalidInputFormat("Missing selected %s language in context creatione (name field)" % language)

    if len(context_name) < 1:
        log.err("Invalid request: name is an empty string")
        raise errors.InvalidInputFormat("Context name is missing (1 char required)")

    if context.escalation_threshold and context.selectable_receiver:
        log.err("Parameter conflict in context creation")
        raise errors.ContextParameterConflict

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            log.err("Creation error: unexistent context can't be associated")
            raise errors.ReceiverGusNotFound
        context.receivers.add(receiver)

    # tip_timetolive and submission_timetolive need to be converted in seconds
    try:
        context.tip_timetolive = utils.seconds_convert(int(request['tip_timetolive']), (24 * 60 * 60), min=1)
    except Exception as excep:
        log.err("Invalid timing configured for Tip: %s" % excep.message)
        raise errors.TimeToLiveInvalid("Submission", excep.message)

    try:
        context.submission_timetolive = utils.seconds_convert(int(request['submission_timetolive']), (60 * 60), min=1)
    except Exception as excep:
        log.err("Invalid timing configured for Submission: %s" % excep.message)
        raise errors.TimeToLiveInvalid("Tip", excep.message)
    # and of timing fixes

    store.add(context)
    return admin_serialize_context(context, language)

@transact
def get_context(store, context_gus, language):
    """
    Returns:
        (dict) the currently configured node.
    """
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
        log.err("Requested invalid context")
        raise errors.ContextGusNotFound

    return admin_serialize_context(context, language)

@transact
def update_context(store, context_gus, request, language):
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

    for receiver in context.receivers:
        context.receivers.remove(receiver)

    receivers = request.get('receivers', [])
    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            log.err("Update error: unexistent receiver can't be associated")
            raise errors.ReceiverGusNotFound
        context.receivers.add(receiver)

    request['name'] = acquire_localized(request['description'], language,
        context.name[language] )
    request['description'] = acquire_localized(request['description'], language,
        context.description[language] )
    request['receipt_description'] = acquire_localized(request['receipt_description'],
        language, context.receipt_description[language] )
    request['submission_introduction'] = acquire_localized(request['submission_introduction'],
        language, context.submission_introduction[language])
    request['submission_disclaimer'] = acquire_localized(request['submission_disclaimer'],
        language, context.submission_disclaimer[language])

    context.update(request)

    # tip_timetolive and submission_timetolive need to be converted in seconds
    try:
        context.tip_timetolive = utils.seconds_convert(context.tip_timetolive, (24 * 60 * 60), min=1)
    except Exception as excep:
        log.err("Invalid timing configured for Tip: %s" % excep.message)
        raise errors.TimeToLiveInvalid("Submission", excep.message)

    try:
        context.submission_timetolive = utils.seconds_convert(context.submission_timetolive, (60 * 60), min=1)
    except Exception as excep:
        log.err("Invalid timing configured for Submission: %s" % excep.message)
        raise errors.TimeToLiveInvalid("Tip", excep.message)
    # and of timing fixes

    context.fields = request['fields']
    context.tags = None # request['tags']
    context.last_update = utils.datetime_now()

    return admin_serialize_context(context, language)

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
def get_receiver_list(store, language):
    """
    Returns:
        (list) the list of receivers
    """
    receiver_list = []

    receivers = store.find(Receiver)
    for receiver in receivers:
        receiver_list.append(admin_serialize_receiver(receiver, language))

    return receiver_list


def create_random_receiver_portrait(receiver_uuid):
    """
    By default take a picture and put in the receiver face,
    we've choose Vittorio Arrigoni portrait, as reference for all the
    nameless journalists around the world, that want spread the truth.
    """
    try:
        shutil.copy(
            os.path.join(GLSetting.static_source, "default-profile-picture.png"),
            os.path.join(GLSetting.static_path, "%s.png" % receiver_uuid)
        )
    except Exception as excep:
        log.err("Unable to copy default receiver portrait in a new receiver! %s" % excep.message)
        raise excep


@transact
def create_receiver(store, request, language):
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

    request['description'] = acquire_localized(request['description'], language)

    receiver = Receiver(request)

    receiver.username = mail_address
    receiver.notification_fields = request['notification_fields']
    receiver.failed_login = 0
    receiver.tags = request['tags']

    # The various options related in manage GPG keys are used here.
    gpg_options_manage(receiver, request)

    log.debug("Creating receiver %s" % (receiver.username))

    security.check_password_format(request['password'])
    receiver.password = security.hash_password(request['password'], mail_address)

    store.add(receiver)
    create_random_receiver_portrait(receiver.id)

    contexts = request.get('contexts', [])
    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        if not context:
            log.err("Creation error: invalid Context can't be associated")
            raise errors.ContextGusNotFound
        context.receivers.add(receiver)

    return admin_serialize_receiver(receiver, language)


@transact
def get_receiver(store, id, language):
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

    return admin_serialize_receiver(receiver, language)


@transact
def update_receiver(store, id, request, language):
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
    receiver.tags = request['tags']

    # The various options related in manage GPG keys are used here.
    gpg_options_manage(receiver, request)

    if len(request['password']):
        security.check_password_format(request['password'])
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
    receiver.last_update = utils.datetime_now()

    return admin_serialize_receiver(receiver, language)

@transact
def delete_receiver(store, id):

    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        log.err("Invalid receiver requested in removal")
        raise errors.ReceiverGusNotFound

    portrait = os.path.join(GLSetting.static_path, "%s.png" % id)

    if os.path.exists(portrait):
        os.unlink(portrait)

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
        node_description = yield get_node(self.request.language)
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

        yield update_node(request, self.request.language)

        # align the memory variables with the new updated data
        yield import_memory_variables()

        node_description = yield get_node(self.request.language)

        self.set_status(202) # Updated
        self.finish(node_description)

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
        response = yield get_context_list(self.request.language)

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

        response = yield create_context(request, self.request.language)

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
        response = yield get_context(context_gus, self.request.language)
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

        response = yield update_context(context_gus, request, self.request.language)

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
        response = yield get_receiver_list(self.request.language)

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

        response = yield create_receiver(request, self.request.language)

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
        response = yield get_receiver(receiver_gus, self.request.language)

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

        response = yield update_receiver(receiver_gus, request, self.request.language)

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

def admin_serialize_notification(notif, language):
    notification_dict = {
        'server': notif.server if notif.server else u"",
        'port': notif.port if notif.port else u"",
        'username': notif.username if notif.username else u"",
        'password': notif.password if notif.password else u"",
        'security': notif.security if notif.security else u"",
        'tip_template': utils.optlang(notif.tip_template, language),
        'tip_mail_title': utils.optlang(notif.tip_mail_title, language),
        'file_template': utils.optlang(notif.file_template, language),
        'file_mail_title': utils.optlang(notif.file_mail_title, language),
        'comment_template': utils.optlang(notif.comment_template, language),
        'comment_mail_title': utils.optlang(notif.comment_mail_title, language),
        'activation_template': utils.optlang(notif.activation_template, language),
        'activation_mail_title': utils.optlang(notif.activation_mail_title, language),
    }
    return notification_dict

@transact
def get_notification(store, language):
    try:
        notif = store.find(Notification).one()
    except Exception as excep:
        log.err("Database error when getting Notification table: %s" % str(excep))
        raise excep

    return admin_serialize_notification(notif, language)

@transact
def update_notification(store, request, language):

    try:
        notif = store.find(Notification).one()
    except Exception as excep:
        log.err("Database error or application error: %s" % excep )
        raise excep

    security = str(request.get('security', u'')).upper()
    if security in Notification._security_types:
        notif.security = security
    else:
        log.err("Invalid request: Security option not recognized")
        raise errors.InvalidInputFormat("Security selection not recognized")

    request['tip_template'] = acquire_localized(request['tip_template'], language,
        notif.tip_template[language] )
    request['file_template'] = acquire_localized(request['file_template'], language,
        notif.file_template[language] )
    request['comment_template'] = acquire_localized(request['comment_template'],
        language, notif.comment_template[language] )

    request['tip_mail_title'] = acquire_localized(request['tip_mail_title'],
        language, notif.tip_mail_title[language])
    request['file_mail_title'] = acquire_localized(request['file_mail_title'],
        language, notif.file_mail_title[language])
    request['comment_mail_title'] = acquire_localized(request['comment_mail_title'],
        language, notif.comment_mail_title[language])

    # temporary hack
    request['activation_mail_title'] = request['activation_template'] = { language : u'' }

    notif.update(request)
    return admin_serialize_notification(notif, language)


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
        notification_desc = yield get_notification(self.request.language)
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

        response = yield update_notification(request, self.request.language)

        self.set_status(202) # Updated
        self.finish(response)

