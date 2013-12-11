# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
import os
import shutil

from Crypto import Random
from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting, sample_context_fields
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import errors, requests
from globaleaks.models import Receiver, Context, Node, Notification, User
from globaleaks import security, models
from globaleaks.utils import utility, structures
from globaleaks.utils.utility import log
from globaleaks.db.datainit import import_memory_variables
from globaleaks.security import gpg_options_parse
from globaleaks import LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED
from globaleaks.third_party import rstr

def admin_serialize_node(node, language=GLSetting.memory_copy.default_language):
    node_dict = {
        "name": node.name,
        "presentation": node.presentation,
        "creation_date": utility.pretty_date_time(node.creation_date),
        "last_update": utility.pretty_date_time(node.last_update),
        "hidden_service": node.hidden_service,
        "public_site": node.public_site,
        "stats_update_time": node.stats_update_time,
        "email": node.email,
        "version": GLSetting.version_string,
        "languages_supported": LANGUAGES_SUPPORTED,
        "languages_enabled": node.languages_enabled,
        "default_language" : node.default_language,
        'maximum_filesize': node.maximum_filesize,
        'maximum_namesize': node.maximum_namesize,
        'maximum_textsize': node.maximum_textsize,
        'exception_email': node.exception_email,
        'tor2web_admin': GLSetting.memory_copy.tor2web_admin,
        'tor2web_submission': GLSetting.memory_copy.tor2web_submission,
        'tor2web_tip': GLSetting.memory_copy.tor2web_tip,
        'tor2web_receiver': GLSetting.memory_copy.tor2web_receiver,
        'tor2web_unauth': GLSetting.memory_copy.tor2web_unauth,
        'postpone_superpower': node.postpone_superpower,
        'can_delete_submission': node.can_delete_submission,
        'reset_css': False,
    }

    mo = structures.Rosetta()
    mo.acquire_storm_object(node)
    for attr in mo.get_localized_attrs():
        node_dict[attr] = mo.dump_translated(attr, language)

    return node_dict

def admin_serialize_context(context, receipt_output, language=GLSetting.memory_copy.default_language):
    context_dict = {
        "context_gus": context.id,
        "creation_date": utility.pretty_date_time(context.creation_date),
        "last_update": utility.pretty_date_time(context.last_update),
        "selectable_receiver": context.selectable_receiver,
        "tip_max_access": context.tip_max_access,
        "file_max_download": context.file_max_download,
        "escalation_threshold": context.escalation_threshold,
        "receivers": [],
        "receipt_regexp": context.receipt_regexp,
        "receipt_example": receipt_output,
        "tags": context.tags if context.tags else [],
        "file_required": context.file_required,
        # tip expressed in day, submission in hours
        "tip_timetolive": context.tip_timetolive / (60 * 60 * 24),
        "submission_timetolive": context.submission_timetolive / (60 * 60),
        "select_all_receivers": context.select_all_receivers,
        "postpone_superpower": context.postpone_superpower,
        "can_delete_submission": context.can_delete_submission,
        "require_file_description": context.require_file_description,
        "delete_consensus_percentage": context.delete_consensus_percentage,
        "maximum_selected_receiver": context.maximum_selected_receiver,
        "require_pgp": context.require_pgp,
    }

    mo = structures.Rosetta()
    mo.acquire_storm_object(context)
    for attr in mo.get_localized_attrs():
        context_dict[attr] = mo.dump_translated(attr, language)

    fo = structures.Fields(context.localized_fields, context.unique_fields)
    context_dict['fields'] = fo.dump_fields(language)

    for receiver in context.receivers:
        context_dict['receivers'].append(receiver.id)

    return context_dict

def admin_serialize_receiver(receiver, language=GLSetting.memory_copy.default_language):
    receiver_dict = {
        "receiver_gus": receiver.id,
        "name": receiver.name,
        "creation_date": utility.pretty_date_time(receiver.creation_date),
        "last_update": utility.pretty_date_time(receiver.last_update),
        "receiver_level": receiver.receiver_level,
        "can_delete_submission": receiver.can_delete_submission,
        "postpone_superpower": receiver.postpone_superpower,
        "username": receiver.user.username,
        'mail_address': receiver.mail_address,
        "failed_login": receiver.user.failed_login_count,
        "password": u"",
        "contexts": [],
        "tags": receiver.tags,
        "gpg_key_info": receiver.gpg_key_info,
        "gpg_key_armor": receiver.gpg_key_armor,
        "gpg_key_remove": False,
        "gpg_key_fingerprint": receiver.gpg_key_fingerprint,
        "gpg_key_status": receiver.gpg_key_status,
        "gpg_enable_notification": True if receiver.gpg_enable_notification else False,
        "gpg_enable_files": True if receiver.gpg_enable_files else False,
        "comment_notification": True if receiver.comment_notification else False,
        "tip_notification": True if receiver.tip_notification else False,
        "file_notification": True if receiver.file_notification else False,
        "message_notification": True if receiver.message_notification else False,
    }

    # only 'description' at the moment is a localized object here
    mo = structures.Rosetta()
    mo.acquire_storm_object(receiver)
    for attr in mo.get_localized_attrs():
        receiver_dict[attr] = mo.dump_translated(attr, language)

    for context in receiver.contexts:
        receiver_dict['contexts'].append(context.id)

    return receiver_dict

@transact_ro
def get_node(store, language=GLSetting.memory_copy.default_language):
    return admin_serialize_node(store.find(Node).one(), language)

@transact
def update_node(store, request, language=GLSetting.memory_copy.default_language):
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

    mo = structures.Rosetta()
    mo.acquire_request(language, request, Node)
    for attr in mo.get_localized_attrs():
        request[attr] = mo.get_localized_dict(attr)

    password = request.get('password', None)
    old_password = request.get('old_password', None)

    if password and old_password and len(password) and len(old_password):
        admin = store.find(User, (User.username == unicode('admin'))).one()
        admin.password = security.change_password(admin.password,
                                    old_password, password, admin.salt)

    if len(request['public_site']) > 1:
        if not utility.acquire_url_address(request['public_site'], hidden_service=True, http=True):
            log.err("Invalid public page regexp in [%s]" % request['public_site'])
            raise errors.InvalidInputFormat("Invalid public site")

    if len(request['hidden_service']) > 1:
        if not utility.acquire_url_address(request['hidden_service'], hidden_service=True, http=False):
            log.err("Invalid hidden service regexp in [%s]" % request['hidden_service'])
            raise errors.InvalidInputFormat("Invalid hidden service")

    # check the 'reset_css' boolean option: remove an existent custom CSS
    if request['reset_css']:
        custom_css_path = os.path.join(GLSetting.static_path, "%s.css" % GLSetting.reserved_names.css)

        if os.path.isfile(custom_css_path):
            try:
                os.remove(custom_css_path)
                log.debug("Reset on custom CSS done.")
            except Exception as excep:
                log.err("Unable to remove custom CSS: %s: %s" % (custom_css_path, excep))
                raise errors.InternalServerError(excep)
        else:
            log.err("Requested CSS Reset, but custom CSS do not exists")

    # verify that the languages enabled are valid 'code' in the languages supported
    node.languages_enabled = []
    for lang_code in request['languages_enabled']:
        if lang_code in LANGUAGES_SUPPORTED_CODES:
            node.languages_enabled.append(lang_code)
        else:
            raise errors.InvalidInputFormat("Invalid lang code enabled: %s" % lang_code)

    if not len(node.languages_enabled):
        raise errors.InvalidInputFormat("Missing enabled languages")

    # enforcing of default_language usage (need to be set, need to be _enabled)
    if request['default_language']:

        if request['default_language'] not in LANGUAGES_SUPPORTED_CODES:
            raise errors.InvalidInputFormat("Invalid lang code as default")

        if request['default_language'] not in node.languages_enabled:
            raise errors.InvalidInputFormat("Invalid lang code as default")

        node.default_language = request['default_language']

    else:
        node.default_language = node.languages_enabled[0]
        log.err("Default language not set!? fallback on %s" % node.default_language)


    # name, description tor2web boolean value are acquired here
    try:
        node.update(request)
    except Exception as dberror:
        log.err("Unable to update Node: %s" % dberror)
        raise errors.InvalidInputFormat(dberror)

    node.last_update = utility.datetime_now()

    return admin_serialize_node(node, language)

@transact_ro
def get_context_list(store, language=GLSetting.memory_copy.default_language):
    """
    Returns:
        (dict) the current context list serialized.
    """
    contexts = store.find(Context)
    context_list = []

    for context in contexts:
        receipt_example = generate_example_receipt(context.receipt_regexp)
        context_list.append(admin_serialize_context(context, receipt_example, language))

    return context_list


def acquire_context_timetolive(request):

    try:
        submission_ttl = utility.seconds_convert(int(request['submission_timetolive']), (60 * 60), min=1)
    except Exception as excep:
        log.err("Invalid timing configured for Submission: %s" % excep.message)
        raise errors.InvalidTipTimeToLive()

    try:
        tip_ttl = utility.seconds_convert(int(request['tip_timetolive']), (24 * 60 * 60), min=1)
    except Exception as excep:
        log.err("Invalid timing configured for Tip: %s" % excep.message)
        raise errors.InvalidSubmTimeToLive()

    if submission_ttl > tip_ttl:
        raise errors.InvalidTipSubmCombo()

    return submission_ttl, tip_ttl

def generate_example_receipt(regexp):
    """
    @param regexp:
    @return:

    this function it's used to show to the Admin an example of the
    receipt_regexp configured, and if an error happen, it's
    works as validator.
    """
    Random.atfork()

    try:
        return_value_receipt = unicode(rstr.xeger(regexp))
    except Exception as excep:
        log.err("Invalid receipt regexp: %s (%s)" % (regexp, excep) )
        raise errors.InvalidReceiptRegexp

    return return_value_receipt

@transact
def create_context(store, request, language=GLSetting.memory_copy.default_language):
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

    mo = structures.Rosetta()
    mo.acquire_request(language, request, Context)
    for attr in mo.get_localized_attrs():
        request[attr] = mo.get_localized_dict(attr)

    context = Context(request)

    if not request['fields']:
        # When a new context is created, assign default fields, if not supply
        admin_data_fields = sample_context_fields
    else:
        admin_data_fields = request['fields']

    try:
        fo = structures.Fields(context.localized_fields, context.unique_fields)
        fo.update_fields(language, admin_data_fields)
        fo.context_import(context)
    except Exception as excep:
        log.err("Unable to create fields: %s" % excep)
        raise excep

    # Integrity checks related on name (need to exists, need to be unique)
    # are performed only using the default language at the moment (XXX)
    try:
        context_name = request['name'][language]
    except Exception as excep:
        raise errors.InvalidInputFormat("language %s do not provide name: %s" %
                                       (language, excep) )

    if len(context_name) < 1:
        log.err("Invalid request: name is an empty string")
        raise errors.InvalidInputFormat("Context name is missing (1 char required)")

    if context.receipt_regexp == u'' or context.receipt_regexp == None:
        log.err("Missing receipt regexp, using default fixme-[0-9]{13}-please")
        context.receipt_regexp = u"fixme-[0-9]{13}-please"

    if context.escalation_threshold and context.selectable_receiver:
        log.err("Parameter conflict in context creation")
        raise errors.ContextParameterConflict

    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            log.err("Creation error: unexistent context can't be associated")
            raise errors.ReceiverGusNotFound
        context.receivers.add(receiver)

    # tip_timetolive and submission_timetolive need to be converted in seconds since hours and days
    (context.submission_timetolive, context.tip_timetolive) = acquire_context_timetolive(request)

    store.add(context)

    receipt_example = generate_example_receipt(context.receipt_regexp)
    return admin_serialize_context(context, receipt_example, language)

@transact_ro
def get_context(store, context_gus, language=GLSetting.memory_copy.default_language):
    """
    Returns:
        (dict) the currently configured node.
    """
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
        log.err("Requested invalid context")
        raise errors.ContextGusNotFound

    receipt_example = generate_example_receipt(context.receipt_regexp)
    return admin_serialize_context(context, receipt_example, language)

@transact
def update_context(store, context_gus, request, language=GLSetting.memory_copy.default_language):
    """
    Updates the specified context. If the key receivers is specified we remove
    the current receivers of the Context and reset set it to the new specified
    ones.
    If no such context exists raises :class:`globaleaks.errors.ContextGusNotFound`.

    Args:
        context_gus:

        request:
            (dict) the request to use to set the attributes of the Context

    Returns:
            (dict) the serialized object updated
    """
    context = store.find(Context, Context.id == unicode(context_gus)).one()

    if not context:
         raise errors.ContextGusNotFound

    mo = structures.Rosetta()
    mo.acquire_request(language, request, Context)
    for attr in mo.get_localized_attrs():
        request[attr] = mo.get_localized_dict(attr)

    for receiver in context.receivers:
        context.receivers.remove(receiver)

    receivers = request.get('receivers', [])
    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        if not receiver:
            log.err("Update error: unexistent receiver can't be associated")
            raise errors.ReceiverGusNotFound
        context.receivers.add(receiver)

    # tip_timetolive and submission_timetolive need to be converted in seconds since hours and days
    (context.submission_timetolive, context.tip_timetolive) = acquire_context_timetolive(request)

    if len(context.receipt_regexp) < 4:
        log.err("Fixing receipt regexp < 4 byte with fixme-[0-9]{13}-please")
        context.receipt_regexp = u"fixme-[0-9]{13}-please"

    try:
        fo = structures.Fields(context.localized_fields, context.unique_fields)
        fo.update_fields(language, request['fields'])
        fo.context_import(context)
    except Exception as excep:
        log.err("Unable to update fields: %s" % excep)
        raise excep

    context.last_update = utility.datetime_now()

    try:
        context.update(request)
    except Exception as dberror:
        log.err("Unable to update context %s: %s" % (context.name, dberror))
        raise errors.InvalidInputFormat(dberror)

    receipt_example = generate_example_receipt(context.receipt_regexp)
    return admin_serialize_context(context, receipt_example, language)

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


@transact_ro
def get_receiver_list(store, language=GLSetting.memory_copy.default_language):
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
def create_receiver(store, request, language=GLSetting.memory_copy.default_language):
    """
    Creates a new receiver.
    Returns:
        (dict) the configured receiver
    """

    mo = structures.Rosetta()
    mo.acquire_request(language, request, Receiver)
    for attr in mo.get_localized_attrs():
        request[attr] = mo.get_localized_dict(attr)

    mail_address = utility.acquire_mail_address(request)
    if not mail_address:
        raise errors.NoEmailSpecified

    # Pretend that username is unique:
    homonymous = store.find(User, User.username == mail_address).count()
    if homonymous:
        log.err("Creation error: already present receiver with the requested username: %s" % mail_address)
        raise errors.ExpectedUniqueField('mail_address', mail_address)

    password = request.get('password')

    security.check_password_format(password)
    receiver_salt = security.get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    receiver_password = security.hash_password(password, receiver_salt)

    receiver_user_dict = {
            'username': mail_address,
            'password': receiver_password,
            'salt': receiver_salt,
            'role': u'receiver',
            'state': u'enabled',
            'failed_login_count': 0,
    }

    receiver_user = models.User(receiver_user_dict)
    receiver_user.last_login = utility.datetime_null()
    store.add(receiver_user)

    receiver = Receiver(request)
    receiver.user = receiver_user

    receiver.mail_address = request.get('mail_address')
    receiver.tags = request.get('tags')

    # The various options related in manage GPG keys are used here.
    gpg_options_parse(receiver, request)

    log.debug("Creating receiver %s" % receiver.user.username)

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


@transact_ro
def get_receiver(store, id, language=GLSetting.memory_copy.default_language):
    """
    raises :class:`globaleaks.errors.ReceiverGusNotFound` if the receiver does
    not exist.
    Returns:
        (dict) the receiver

    """
    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        log.err("Requested in receiver")
        raise errors.ReceiverGusNotFound

    return admin_serialize_receiver(receiver, language)


@transact
def update_receiver(store, id, request, language=GLSetting.memory_copy.default_language):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverGusNotFound` if the receiver does
    not exist.
    """
    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        raise errors.ReceiverGusNotFound

    mo = structures.Rosetta()
    mo.acquire_request(language, request, Receiver)
    for attr in mo.get_localized_attrs():
        request[attr] = mo.get_localized_dict(attr)

    mail_address = utility.acquire_mail_address(request)
    if not mail_address:
        raise errors.NoEmailSpecified

    homonymous = store.find(User, User.username == mail_address).one()
    if homonymous and homonymous.id != receiver.user_id:
        log.err("Update error: already present receiver with the requested username: %s" % mail_address)
        raise errors.ExpectedUniqueField('mail_address', mail_address)

    receiver.mail_address = request['mail_address']
    receiver.tags = request['tags']

    # the email address it's also the username, stored in User
    receiver.user.username = mail_address

    # The various options related in manage GPG keys are used here.
    gpg_options_parse(receiver, request)

    password = request.get('password')
    if len(password):
        security.check_password_format(password)
        receiver.user.password = security.hash_password(password, receiver.user.salt)

    contexts = request.get('contexts', [])

    for context in receiver.contexts:
        receiver.contexts.remove(context)

    for context_id in contexts:
        context = store.find(Context, Context.id == context_id).one()
        if not context:
            log.err("Update error: unexistent context can't be associated")
            raise errors.ContextGusNotFound
        receiver.contexts.add(context)

    receiver.last_update = utility.datetime_now()
    try:
        receiver.update(request)
    except Exception as dberror:
        log.err("Unable to update receiver %s: %s" % (receiver.name, dberror))
        raise errors.InvalidInputFormat(dberror)

    return admin_serialize_receiver(receiver, language)

@transact
def delete_receiver(store, id):

    receiver = store.find(Receiver, Receiver.id == unicode(id)).one()

    if not receiver:
        log.err("Invalid receiver requested in removal")
        raise errors.ReceiverGusNotFound

    portrait = os.path.join(GLSetting.static_path, "%s.png" % id)

    if os.path.exists(portrait):
        os.remove(portrait)

    store.remove(receiver.user)


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
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNodeDesc
        Errors: NodeNotFound
        """
        node_description = yield get_node(self.request.language)
        self.set_status(200)
        self.finish(node_description)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
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
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminContextList
        Errors: None
        """
        response = yield get_context_list(self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ReceiverGusNotFound
        """
        #request = self.validate_message(self.request.body, requests.adminContextDesc)
        import json
        request = json.loads(self.request.body)
        # AAA TODO REMIND CRITIC TEST

        response = yield create_context(request, self.request.language)

        self.set_status(201) # Created
        self.finish(response)

class ContextInstance(BaseHandler):
    """
    A3
    classic CRUD in the single Context resource.
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, context_gus, *uriargs):
        """
        Parameters: context_gus
        Response: adminContextDesc
        Errors: ContextGusNotFound, InvalidInputFormat
        """
        response = yield get_context(context_gus, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
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

    @transport_security_check('admin')
    @authenticated('admin')
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

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
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

    @transport_security_check('admin')
    @authenticated('admin')
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

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
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

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
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

def admin_serialize_notification(notif, language=GLSetting.memory_copy.default_language):
    notification_dict = {
        'server': notif.server if notif.server else u"",
        'port': notif.port if notif.port else u"",
        'username': notif.username if notif.username else u"",
        'password': notif.password if notif.password else u"",
        'security': notif.security if notif.security else u"",
        'source_name' : notif.source_name,
        'source_email' : notif.source_email,
        'disable': GLSetting.notification_temporary_disable,
    }

    mo = structures.Rosetta()
    mo.acquire_storm_object(notif)
    for attr in mo.get_localized_attrs():
        notification_dict[attr] = mo.dump_translated(attr, language)

    return notification_dict

@transact_ro
def get_notification(store, language=GLSetting.memory_copy.default_language):
    try:
        notif = store.find(Notification).one()
    except Exception as excep:
        log.err("Database error when getting Notification table: %s" % str(excep))
        raise excep

    return admin_serialize_notification(notif, language)

@transact
def update_notification(store, request, language=GLSetting.memory_copy.default_language):

    try:
        notif = store.find(Notification).one()
    except Exception as excep:
        log.err("Database error or application error: %s" % excep )
        raise excep

    mo = structures.Rosetta()
    mo.acquire_request(language, request, Notification)
    for attr in mo.get_localized_attrs():
        request[attr] = mo.get_localized_dict(attr)

    if request['security'] in Notification._security_types:
        notif.security = request['security']
    else:
        log.err("Invalid request: Security option not recognized")
        log.debug("Invalid Security value: %s" % request['security'])
        raise errors.InvalidInputFormat("Security selection not recognized")

    try:
        notif.update(request)
    except Exception as dberror:
        log.err("Unable to update Notification: %s" % dberror)
        raise errors.InvalidInputFormat(dberror)

    if request['disable'] != GLSetting.notification_temporary_disable:
        log.msg("Switching notification mode: was %s and now is %s" %
                ("DISABLE" if GLSetting.notification_temporary_disable else "ENABLE",
                 "DISABLE" if request['disable'] else "ENABLE")
        )
        GLSetting.notification_temporary_disable = request['disable']

    return admin_serialize_notification(notif, language)


class NotificationInstance(BaseHandler):
    """
    A6

    Manage Notification settings (account details and template)
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNotificationDesc
        Errors: None (return empty configuration, at worst)
        """
        notification_desc = yield get_notification(self.request.language)
        self.set_status(200)
        self.finish(notification_desc)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
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

        # align the memory variables with the new updated data
        yield import_memory_variables()

        self.set_status(202) # Updated
        self.finish(response)

