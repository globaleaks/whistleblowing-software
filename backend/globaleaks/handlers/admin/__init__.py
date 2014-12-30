# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
import copy
import os
import shutil

from storm.exceptions import DatabaseError
from twisted.internet.defer import inlineCallbacks

from globaleaks import security, LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED
from globaleaks.db.datainit import db_import_memory_variables
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler, GLApiCache
from globaleaks.handlers.admin.field import disassociate_field, get_field_association
from globaleaks.handlers.node import get_public_context_list, get_public_receiver_list, \
    anon_serialize_node, anon_serialize_step, anon_serialize_field
from globaleaks import models
from globaleaks.rest import errors, requests
from globaleaks.security import gpg_options_parse
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.third_party import rstr
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now, datetime_null, seconds_convert, datetime_to_ISO8601


def db_admin_serialize_node(store, language):

    node = store.find(models.Node).one()

    admin = store.find(models.User, (models.User.username == unicode('admin'))).one()

    # Contexts and Receivers relationship
    associated = store.find(models.ReceiverContext).count()
    custom_homepage = os.path.isfile(os.path.join(GLSetting.static_path, "custom_homepage.html"))

    ret_dict = {
        "name": node.name,
        "presentation": node.presentation,
        "creation_date": datetime_to_ISO8601(node.creation_date),
        "last_update": datetime_to_ISO8601(node.last_update),
        "hidden_service": node.hidden_service,
        "public_site": node.public_site,
        "stats_update_time": node.stats_update_time,
        "email": node.email,
        "version": GLSetting.version_string,
        "languages_supported": LANGUAGES_SUPPORTED,
        "languages_enabled": node.languages_enabled,
        "default_language" : node.default_language,
        'default_timezone' : node.default_timezone,
        'maximum_filesize': node.maximum_filesize,
        'maximum_namesize': node.maximum_namesize,
        'maximum_textsize': node.maximum_textsize,
        'exception_email': node.exception_email,
        'tor2web_admin': GLSetting.memory_copy.tor2web_admin,
        'tor2web_submission': GLSetting.memory_copy.tor2web_submission,
        'tor2web_receiver': GLSetting.memory_copy.tor2web_receiver,
        'tor2web_unauth': GLSetting.memory_copy.tor2web_unauth,
        'postpone_superpower': node.postpone_superpower,
        'can_delete_submission': node.can_delete_submission,
        'ahmia': node.ahmia,
        'reset_css': False,
        'reset_homepage': False,
        'allow_unencrypted': node.allow_unencrypted,
        'wizard_done': node.wizard_done,
        'configured': True if associated else False,
        'password': u"",
        'old_password': u"",
        'custom_homepage': custom_homepage,
        'disable_privacy_badge': node.disable_privacy_badge,
        'disable_security_awareness_badge': node.disable_security_awareness_badge,
        'disable_security_awareness_questions': node.disable_security_awareness_questions,
        'admin_language': admin.language,
        'admin_timezone': admin.timezone,
        'enable_custom_privacy_badge': node.enable_custom_privacy_badge,
        'custom_privacy_badge_tbb': node.custom_privacy_badge_tbb,
        'custom_privacy_badge_tor': node.custom_privacy_badge_tor,
        'custom_privacy_badge_none': node.custom_privacy_badge_none,
    }

    return get_localized_values(ret_dict, node, node.localized_strings, language)

@transact_ro
def admin_serialize_node(*args):
    return db_admin_serialize_node(*args)

def db_create_step(store, context_id, steps, language):
    """
    Add a new step to the store, then return the new serialized object.
    """
    context = models.Context.get(store, context_id)
    if context is None:
        raise errors.ContextIdNotFound

    n = 1
    for step in steps:
        step['context_id'] = context_id
        step['number'] = n

        fill_localized_keys(step, models.Step.localized_strings, language)

        s = models.Step.new(store, step)
        for f in step['children']:
            field = models.Field.get(store, f['id'])
            if not field:
                log.err("Creation error: unexistent field can't be associated")
                raise errors.FieldIdNotFound

            # remove current step/field fieldgroup/field association
            a_s, _ = get_field_association(store, field.id)
            if a_s != s.id:
                disassociate_field(store, field.id)
                s.children.add(field)

        n += 1

def db_update_steps(store, context_id, steps, language):
    """
    Update steps removing old field associated and recreating new.
    """
    context = models.Context.get(store, context_id)
    if context is None:
        raise errors.ContextIdNotFound

    old_steps = store.find(models.Step, models.Step.context_id == context_id)

    indexed_old_steps = {}
    for o in old_steps:
        indexed_old_steps[o.id] = o

    new_steps = []
    n = 1
    for step in steps:
        step['context_id'] = context_id
        step['number'] = n

        fill_localized_keys(step, models.Step.localized_strings, language)

        # check for reuse (needed to keep translations)
        if 'id' in step and step['id'] in indexed_old_steps:
            s = indexed_old_steps[step['id']]
            for field in s.children:
                s.children.remove(field)

            s.update(step)

            new_steps.append(indexed_old_steps[step['id']])
            del indexed_old_steps[step['id']]
        else:
            new_steps.append(models.Step(step))

        i = 1
        for f in step['children']:
            field = models.Field.get(store, f['id'])
            i += 1
            field.y = i
            if not field:
                log.err("Creation error: unexistent field can't be associated")
                raise errors.FieldIdNotFound

            # remove current step/field fieldgroup/field association
            a_s, _ = get_field_association(store, field.id)
            if a_s is None:
                s.children.add(field)
            elif a_s != s.id:
                disassociate_field(store, field.id)
                s.children.add(field)
            else: # the else condition means a_s == s.id; already associated!
                pass

        n += 1

    for o_id in indexed_old_steps:
        store.remove(indexed_old_steps[o_id])

    for n in new_steps:
        store.add(n)

def admin_serialize_context(store, context, language):

    steps = [ anon_serialize_step(store, s, language)
              for s in context.steps.order_by(models.Step.number) ]

    ret_dict = {
        "id": context.id,
        "creation_date": datetime_to_ISO8601(context.creation_date),
        "last_update": datetime_to_ISO8601(context.last_update),
	"selectable_receiver": context.selectable_receiver,
        "tip_max_access": context.tip_max_access,
        "file_max_download": context.file_max_download,
        "receivers": [r.id for r in context.receivers],
        # tip expressed in day, submission in hours
        "tip_timetolive": context.tip_timetolive / (60 * 60 * 24),
        "submission_timetolive": context.submission_timetolive / (60 * 60),
        "select_all_receivers": context.select_all_receivers,
        "postpone_superpower": context.postpone_superpower,
        "can_delete_submission": context.can_delete_submission,
        "maximum_selectable_receivers": context.maximum_selectable_receivers,
        "show_small_cards": context.show_small_cards,
        "show_receivers": context.show_receivers,
        "enable_private_messages": context.enable_private_messages,
        "presentation_order": context.presentation_order,
        "steps": steps
    }

    return get_localized_values(ret_dict, context, context.localized_strings, language)

def admin_serialize_receiver(receiver, language):

    ret_dict = {
        "id": receiver.id,
        "name": receiver.name,
        "creation_date": datetime_to_ISO8601(receiver.creation_date),
        "last_update": datetime_to_ISO8601(receiver.last_update),
        "can_delete_submission": receiver.can_delete_submission,
        "postpone_superpower": receiver.postpone_superpower,
        "username": receiver.user.username,
        "user_id": receiver.user.id,
        'mail_address': receiver.mail_address,
        "password": u"",
        "state": receiver.user.state,
        "configuration": receiver.configuration,
        "contexts": [c.id for c in receiver.contexts],
        "gpg_key_info": receiver.gpg_key_info,
        "gpg_key_armor": receiver.gpg_key_armor,
        "gpg_key_remove": False,
        "gpg_key_fingerprint": receiver.gpg_key_fingerprint,
        "gpg_key_status": receiver.gpg_key_status,
        "gpg_enable_notification": True if receiver.gpg_enable_notification else False,
        "comment_notification": True if receiver.comment_notification else False,
        "tip_notification": True if receiver.tip_notification else False,
        "file_notification": True if receiver.file_notification else False,
        "message_notification": True if receiver.message_notification else False,
        "presentation_order": receiver.presentation_order,
        "language": receiver.user.language,
        "timezone": receiver.user.timezone,
        "password_change_needed": receiver.user.password_change_needed
    }

    return get_localized_values(ret_dict, receiver, receiver.localized_strings, language)

def db_update_node(store, request, wizard_done, language):
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
    node = store.find(models.Node).one()

    fill_localized_keys(request, models.Node.localized_strings, language)

    admin = store.find(models.User, (models.User.username == unicode('admin'))).one()

    admin.language = request.get('admin_language', GLSetting.memory_copy.default_language)
    admin.timezone = request.get('admin_timezone', GLSetting.memory_copy.default_timezone)

    password = request.get('password', None)
    old_password = request.get('old_password', None)

    if password and old_password and len(password) and len(old_password):
        admin.password = security.change_password(admin.password,
                                    old_password, password, admin.salt)

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
            log.err("Requested CSS Reset, but custom CSS does not exist")

    # check the 'reset_homepage' boolean option: remove an existent custom Homepage
    if request['reset_homepage']:
        custom_homepage_path = os.path.join(GLSetting.static_path, "%s.html" % GLSetting.reserved_names.html)

        if os.path.isfile(custom_homepage_path):
            try:
                os.remove(custom_homepage_path)
                log.debug("Reset on custom Homepage done.")
            except Exception as excep:
                log.err("Unable to remove custom Homepage: %s: %s" % (custom_homepage_path, excep))
                raise errors.InternalServerError(excep)
        else:
            log.err("Requested Homepage Reset, but custom Homepage does not exist")

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

    # default False in creation, default False in the option.
    if wizard_done:
        if node.wizard_done:
            log.err("wizard completed more than one time!?")
        else:
            log.debug("wizard completed: Node initialized")
            node.wizard_done = True

    # since change of regexp format to XXXX-XXXX-XXXX-XXXX
    # we removed the possibility to customize the receipt from the GLCllient
    request['receipt_regexp'] = GLSetting.defaults.receipt_regexp

    try:
        node.update(request)
    except DatabaseError as dberror:
        log.err("Unable to update Node: %s" % dberror)
        raise errors.InvalidInputFormat(dberror)

    node.last_update = datetime_now()

    db_import_memory_variables(store)

    return db_admin_serialize_node(store, language)

@transact
def update_node(*args):
    return db_update_node(*args)

@transact_ro
def get_context_list(store, language):
    """
    Returns:
        (dict) the current context list serialized.
    """
    contexts = store.find(models.Context)
    context_list = []

    for context in contexts:
        context_list.append(admin_serialize_context(store, context, language))

    return context_list


def acquire_context_timetolive(request):

    try:
        submission_ttl = seconds_convert(int(request['submission_timetolive']), (60 * 60), minv=1)
    except Exception as excep:
        log.err("Invalid timing configured for Submission: %s" % excep.message)
        raise errors.InvalidTipTimeToLive()

    try:
        tip_ttl = seconds_convert(int(request['tip_timetolive']), (24 * 60 * 60), minv=1)
    except Exception as excep:
        log.err("Invalid timing configured for Tip: %s" % excep.message)
        raise errors.InvalidSubmTimeToLive()

    if submission_ttl > tip_ttl:
        raise errors.InvalidTipSubmCombo()

    return submission_ttl, tip_ttl

def field_is_present(store, field):
    result = store.find(models.Field,
                        models.Field.label == field['label'],
                        models.Field.description == field['description'],
                        models.Field.hint == field['hint'],
                        models.Field.multi_entry == field['multi_entry'],
                        models.Field.type == field['type'],
                        models.Field.preview == field['preview'])
    return result.count() > 0


def db_create_context(store, request, language):
    """
    Creates a new context from the request of a client.

    We associate to the context the list of receivers and if the receiver is
    not valid we raise a ReceiverIdNotFound exception.

    Args:
        (dict) the request containing the keys to set on the model.

    Returns:
        (dict) representing the configured context
    """
    receivers = request.get('receivers', [])
    steps = request.get('steps', [])

    fill_localized_keys(request, models.Context.localized_strings, language)

    context = models.Context(request)

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

    if request['select_all_receivers']:
        if request['maximum_selectable_receivers']:
            log.debug("Resetting maximum_selectable_receivers (%d) because 'select_all_receivers' is True" %
                      request['maximum_selectable_receivers'])
        request['maximum_selectable_receivers'] = 0

    # tip_timetolive and submission_timetolive need to be converted in seconds since hours and days
    (context.submission_timetolive, context.tip_timetolive) = acquire_context_timetolive(request)

    c = store.add(context)

    for receiver_id in receivers:
        receiver = models.Receiver.get(store, receiver_id)
        if not receiver:
            log.err("Creation error: unexistent context can't be associated")
            raise errors.ReceiverIdNotFound
        c.receivers.add(receiver)

    if steps:
        db_create_step(store, context.id, steps, language)
    else:
        appdata = store.find(models.ApplicationData).one()
        steps = copy.deepcopy(appdata.fields)
        n_s = 1
        for step in steps:
            for f_child in step['children']:
                if not field_is_present(store, f_child):
                    f_child['is_template'] = False
        for step in steps:
            f_children = copy.deepcopy(step['children'])
            del step['children']
            s = models.db_forge_obj(store, models.Step, step)
            for f_child in f_children:
                o_children = copy.deepcopy(f_child['options'])
                del f_child['options']
                # FIXME currently default updata do not handle fieldgroups
                # all this block must be redesigned in order to be called recursively
                del f_child['children']
                f = models.db_forge_obj(store, models.Field, f_child)
                n_o = 1
                for o_child in o_children:
                    o = models.db_forge_obj(store, models.FieldOption, o_child)
                    o.field_id = f.id
                    o.number = n_o
                    f.options.add(o)
                    n_o += 1
                f.step_id = s.id
                s.children.add(f)
            s.context_id = context.id
            s.number = n_s
            context.steps.add(s)
            n_s += 1

    log.debug("Created context %s (using %s)" % (context_name, language) )

    return admin_serialize_context(store, context, language)

@transact
def create_context(*args):
    return db_create_context(*args)

@transact_ro
def get_context(store, context_id, language):
    """
    Returns:
        (dict) the context with the specified id.
    """
    context = store.find(models.Context, models.Context.id == context_id).one()

    if not context:
        log.err("Requested invalid context")
        raise errors.ContextIdNotFound

    return admin_serialize_context(store, context, language)

def db_get_fields_recursively(store, field, language):
    ret = []
    for children in field.children:
        s = anon_serialize_field(store, children, language)
        ret.append(s)
        ret += db_get_fields_recursively(store, children, language)

    return ret

def db_get_context_steps(store, context_id, language):
    """
    Returns:
        (dict) the steps associated with the context with the specified id.
    """

    context = store.find(models.Context, models.Context.id == context_id).one()

    if not context:
        log.err("Requested invalid context")
        raise errors.ContextIdNotFound

    return [anon_serialize_step(store, s, language) for s in context.steps]

@transact_ro
def get_context_steps(*args):
    return db_get_context_steps(*args)

@transact
def update_context(store, context_id, request, language):
    """
    Updates the specified context. If the key receivers is specified we remove
    the current receivers of the Context and reset set it to the new specified
    ones.
    If no such context exists raises :class:`globaleaks.errors.ContextIdNotFound`.

    Args:
        context_id:

        request:
            (dict) the request to use to set the attributes of the Context

    Returns:
            (dict) the serialized object updated
    """
    context = store.find(models.Context, models.Context.id == context_id).one()

    if not context:
         raise errors.ContextIdNotFound

    receivers = request.get('receivers', [])
    steps = request.get('steps', [])

    fill_localized_keys(request, models.Context.localized_strings, language)

    for receiver in context.receivers:
        context.receivers.remove(receiver)

    for receiver_id in receivers:
        receiver = store.find(models.Receiver, models.Receiver.id == receiver_id).one()
        if not receiver:
            log.err("Update error: unexistent receiver can't be associated")
            raise errors.ReceiverIdNotFound
        context.receivers.add(receiver)

    # tip_timetolive and submission_timetolive need to be converted in seconds since hours and days
    (context.submission_timetolive, context.tip_timetolive) = acquire_context_timetolive(request)

    if request['select_all_receivers']:
        if request['maximum_selectable_receivers']:
            log.debug("Resetting maximum_selectable_receivers (%d) because 'select_all_receivers' is True" %
                       request['maximum_selectable_receivers'])
        request['maximum_selectable_receivers'] = 0

    context.last_update = datetime_now()

    try:
        context.update(request)
    except DatabaseError as dberror:
        log.err("Unable to update context %s: %s" % (context.name, dberror))
        raise errors.InvalidInputFormat(dberror)

    db_update_steps(store, context.id, steps, language)

    return admin_serialize_context(store, context, language)

@transact
def delete_context(store, context_id):
    """
    Deletes the specified context. If no such context exists raises
    :class:`globaleaks.errors.ContextIdNotFound`.

    Args:
        context_id: the context id of the context to remove.
    """
    context = store.find(models.Context, models.Context.id == context_id).one()

    if not context:
        log.err("Invalid context requested in removal")
        raise errors.ContextIdNotFound

    store.remove(context)


@transact_ro
def get_receiver_list(store, language):
    """
    Returns:
        (list) the list of receivers
    """
    receiver_list = []

    receivers = store.find(models.Receiver)
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


def db_create_receiver(store, request, language):
    """
    Creates a new receiver.
    Returns:
        (dict) the configured receiver
    """

    fill_localized_keys(request, models.Receiver.localized_strings, language)

    mail_address = request['mail_address']

    # Pretend that username is unique:
    homonymous = store.find(models.User, models.User.username == mail_address).count()
    if homonymous:
        log.err("Creation error: already present receiver with the requested username: %s" % mail_address)
        raise errors.ExpectedUniqueField('mail_address', mail_address)

    password = request['password']
    if len(password) and password != GLSetting.default_password:
        security.check_password_format(password)
    else:
        password = GLSetting.default_password

    receiver_salt = security.get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    receiver_password = security.hash_password(password, receiver_salt)

    receiver_user_dict = {
        'username': mail_address,
        'password': receiver_password,
        'salt': receiver_salt,
        'role': u'receiver',
        'state': u'enabled',
        'language': u"en",
        'timezone': 0,
        'password_change_needed': True,
    }

    receiver_user = models.User(receiver_user_dict)
    receiver_user.last_login = datetime_null()
    receiver_user.password_change_needed = request['password_change_needed']
    receiver_user.password_change_date = datetime_null()
    store.add(receiver_user)

    receiver = models.Receiver(request)
    receiver.user = receiver_user

    receiver.mail_address = mail_address

    # The various options related in manage GPG keys are used here.
    gpg_options_parse(receiver, request)

    log.debug("Creating receiver %s" % receiver.user.username)

    store.add(receiver)

    create_random_receiver_portrait(receiver.id)

    contexts = request.get('contexts', [])
    for context_id in contexts:
        context = models.Context.get(store, context_id)
        if not context:
            log.err("Creation error: invalid Context can't be associated")
            raise errors.ContextIdNotFound
        context.receivers.add(receiver)

    return admin_serialize_receiver(receiver, language)

@transact
def create_receiver(*args):
    return db_create_receiver(*args)

@transact_ro
def get_receiver(store, receiver_id, language):
    """
    raises :class:`globaleaks.errors.ReceiverIdNotFound` if the receiver does
    not exist.
    Returns:
        (dict) the receiver

    """
    receiver = models.Receiver.get(store, receiver_id)

    if not receiver:
        log.err("Requested in receiver")
        raise errors.ReceiverIdNotFound

    return admin_serialize_receiver(receiver, language)


@transact
def update_receiver(store, receiver_id, request, language):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverIdNotFound` if the receiver does
    not exist.
    """
    receiver = models.Receiver.get(store, receiver_id)

    if not receiver:
        raise errors.ReceiverIdNotFound

    fill_localized_keys(request, models.Receiver.localized_strings, language)

    mail_address = request['mail_address']

    homonymous = store.find(models.User, models.User.username == mail_address).one()
    if homonymous and homonymous.id != receiver.user_id:
        log.err("Update error: already present receiver with the requested username: %s" % mail_address)
        raise errors.ExpectedUniqueField('mail_address', mail_address)

    receiver.mail_address = mail_address

    # the email address it's also the username, stored in User
    receiver.user.username = mail_address

    receiver.user.state = request['state']

    # The various options related in manage GPG keys are used here.
    gpg_options_parse(receiver, request)

    receiver.user.language = request.get('language', GLSetting.memory_copy.default_language)
    receiver.user.timezone = request.get('timezone', GLSetting.memory_copy.default_timezone)

    password = request['password']
    if len(password):
        security.check_password_format(password)
        receiver.user.password = security.hash_password(password, receiver.user.salt)
        receiver.user.password_change_date = datetime_now()

    contexts = request.get('contexts', [])

    for context in receiver.contexts:
        receiver.contexts.remove(context)

    for context_id in contexts:
        context = models.Context.get(store, context_id)
        if not context:
            log.err("Update error: unexistent context can't be associated")
            raise errors.ContextIdNotFound
        receiver.contexts.add(context)

    receiver.last_update = datetime_now()
    try:
        receiver.update(request)
    except DatabaseError as dberror:
        log.err("Unable to update receiver %s: %s" % (receiver.name, dberror))
        raise errors.InvalidInputFormat(dberror)

    return admin_serialize_receiver(receiver, language)

@transact
def delete_receiver(store, receiver_id):

    receiver = models.Receiver.get(store, receiver_id)

    if not receiver:
        log.err("Invalid receiver requested in removal")
        raise errors.ReceiverIdNotFound

    portrait = os.path.join(GLSetting.static_path, "%s.png" % receiver_id)

    if os.path.exists(portrait):
        os.remove(portrait)

    store.remove(receiver.user)


# ---------------------------------
# Below starts the Cyclone handlers
# ---------------------------------


class NodeInstance(BaseHandler):
    """
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    /node
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: adminNodeDesc
        Errors: NodeNotFound
        """
        node_description = yield admin_serialize_node(self.request.language)
        self.set_status(200)
        self.finish(node_description)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self):
        """
        Request: adminNodeDesc
        Response: adminNodeDesc
        Errors: InvalidInputFormat

        Changes the node public node configuration settings.
        """
        request = self.validate_message(self.request.body,
                requests.adminNodeDesc)

        node_description = yield update_node(request, True, self.request.language)

        # update 'node' cache calling the 'public' side of /node
        public_node_desc = yield anon_serialize_node(self.request.language)
        GLApiCache.invalidate('node')
        GLApiCache.set('node', self.request.language, public_node_desc)

        self.set_status(202) # Updated
        self.finish(node_description)

class ContextsCollection(BaseHandler):
    """
    Return a list of all the available contexts, in elements.

    /admin/context
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
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
    def post(self):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        request = self.validate_message(self.request.body, requests.adminContextDesc)

        response = yield create_context(request, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')
        GLApiCache.set('contexts', self.request.language, public_contexts_list)

        # contexts update causes also receivers update
        GLApiCache.invalidate('receivers')

        self.set_status(201) # Created
        self.finish(response)

class ContextInstance(BaseHandler):
    """
    classic CRUD in the single Context resource.
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, context_id):
        """
        Parameters: context_id
        Response: adminContextDesc
        Errors: ContextIdNotFound, InvalidInputFormat
        """
        response = yield get_context(context_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, context_id):
        """
        Request: adminContextDesc
        Response: adminContextDesc
        Errors: InvalidInputFormat, ContextIdNotFound, ReceiverIdNotFound
        """

        request = self.validate_message(self.request.body,
                                        requests.adminContextDesc)

        response = yield update_context(context_id, request, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')
        GLApiCache.set('contexts', self.request.language, public_contexts_list)

        # contexts update causes also receivers update
        GLApiCache.invalidate('receivers')

        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, context_id):
        """
        Request: adminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextIdNotFound
        """
        yield delete_context(context_id)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')
        GLApiCache.set('contexts', self.request.language, public_contexts_list)

        # contexts update causes also receivers update
        GLApiCache.invalidate('receivers')

        self.set_status(200) # Ok and return no content
        self.finish()

class ReceiversCollection(BaseHandler):
    """
    List all available receivers present in the node.
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
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
    def post(self):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ContextIdNotFound

        Create a new receiver
        """
        request = self.validate_message(self.request.body,
                requests.adminReceiverDesc)

        response = yield create_receiver(request, self.request.language)

        # get the updated list of receivers, and update the cache
        public_receivers_list = yield get_public_receiver_list(self.request.language)
        GLApiCache.invalidate('receivers')
        GLApiCache.set('receivers', self.request.language, public_receivers_list)

        # receivers update causes also contexts update
        GLApiCache.invalidate('contexts')

        self.set_status(201) # Created
        self.finish(response)

class ReceiverInstance(BaseHandler):
    """
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
    def get(self, receiver_id):
        """
        Parameters: receiver_id
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound

        Get an existent Receiver instance.
        """
        response = yield get_receiver(receiver_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, receiver_id):
        """
        Request: adminReceiverDesc
        Response: adminReceiverDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound, ContextId

        Update information about a Receiver, return the instance updated.
        """
        request = self.validate_message(self.request.body, requests.adminReceiverDesc)

        response = yield update_receiver(receiver_id, request, self.request.language)

        # get the updated list of receivers, and update the cache
        public_receivers_list = yield get_public_receiver_list(self.request.language)
        GLApiCache.invalidate('receivers')
        GLApiCache.set('receivers', self.request.language, public_receivers_list)

        # receivers update causes also contexts update
        GLApiCache.invalidate('contexts')

        self.set_status(201)
        self.finish(response)

    @inlineCallbacks
    @transport_security_check('admin')
    @authenticated('admin')
    def delete(self, receiver_id):
        """
        Parameter: receiver_id
        Request: None
        Response: None
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        yield delete_receiver(receiver_id)

        # get the updated list of receivers, and update the cache
        public_receivers_list = yield get_public_receiver_list(self.request.language)
        GLApiCache.invalidate('receivers')
        GLApiCache.set('receivers', self.request.language, public_receivers_list)

        # receivers update causes also contexts update
        GLApiCache.invalidate('contexts')

        self.set_status(200) # OK and return not content
        self.finish()
