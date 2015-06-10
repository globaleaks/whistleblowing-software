# -*- coding: UTF-8
#
#   admin
#   *****
# Implementation of the code executed when an HTTP client reach /admin/* URI
#
import copy
import shutil
from storm.exceptions import DatabaseError

from globaleaks import models, security, LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED
from globaleaks.handlers.admin.field import disassociate_field, get_field_association
from globaleaks.handlers.admin.langfiles import *
from globaleaks.handlers.admin.staticfiles import *
from globaleaks.handlers.admin.overview import *
from globaleaks.handlers.admin.statistics import *
from globaleaks.handlers.admin.notification import *
from globaleaks.handlers.node import anon_serialize_step
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import GLBPGP
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.third_party import rstr
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now, datetime_null, datetime_to_ISO8601, uuid4


def db_admin_serialize_node(store, language):
    """
    Serialize node infos.

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary including the node configuration.
    """
    node = store.find(models.Node).one()

    admin = store.find(models.User, (models.User.username == unicode('admin'))).one()

    # Contexts and Receivers relationship
    configured  = store.find(models.ReceiverContext).count() > 0

    custom_homepage = os.path.isfile(os.path.join(GLSetting.static_path, "custom_homepage.html"))

    ret_dict = {
        'name': node.name,
        'presentation': node.presentation,
        'creation_date': datetime_to_ISO8601(node.creation_date),
        'last_update': datetime_to_ISO8601(node.last_update),
        'hidden_service': node.hidden_service,
        'public_site': node.public_site,
        'email': node.email,
        'version': GLSetting.version_string,
        'languages_supported': LANGUAGES_SUPPORTED,
        'languages_enabled': node.languages_enabled,
        'default_language' : node.default_language,
        'default_timezone' : node.default_timezone,
        'maximum_filesize': node.maximum_filesize,
        'maximum_namesize': node.maximum_namesize,
        'maximum_textsize': node.maximum_textsize,
        'exception_email': node.exception_email,
        'tor2web_admin': GLSetting.memory_copy.tor2web_admin,
        'tor2web_submission': GLSetting.memory_copy.tor2web_submission,
        'tor2web_receiver': GLSetting.memory_copy.tor2web_receiver,
        'tor2web_unauth': GLSetting.memory_copy.tor2web_unauth,
        'submission_minimum_delay' : GLSetting.memory_copy.submission_minimum_delay,
        'submission_maximum_ttl' : GLSetting.memory_copy.submission_maximum_ttl,
        'can_postpone_expiration': node.can_postpone_expiration,
        'can_delete_submission': node.can_delete_submission,
        'ahmia': node.ahmia,
        'allow_unencrypted': node.allow_unencrypted,
        'allow_iframes_inclusion': node.allow_iframes_inclusion,
        'wizard_done': node.wizard_done,
        'configured': configured,
        'password': u'',
        'old_password': u'',
        'custom_homepage': custom_homepage,
        'disable_privacy_badge': node.disable_privacy_badge,
        'disable_security_awareness_badge': node.disable_security_awareness_badge,
        'disable_security_awareness_questions': node.disable_security_awareness_questions,
        'disable_key_code_hint': node.disable_key_code_hint,
        'admin_language': admin.language,
        'admin_timezone': admin.timezone,
        'enable_custom_privacy_badge': node.enable_custom_privacy_badge,
        'landing_page': node.landing_page,
        'show_contexts_in_alphabetical_order': node.show_contexts_in_alphabetical_order
    }

    return get_localized_values(ret_dict, node, node.localized_strings, language)


@transact_ro
def admin_serialize_node(*args):
    return db_admin_serialize_node(*args)


def db_admin_serialize_user(store, username):
    """
    Serialize user description

    :param store: the store on which perform queries.
    :param username: the username of the user to be serialized
    :return: a serialization of the object
    """
    user = store.find(models.User, models.User.username == unicode(username)).one()

    ret_dict = {
        'username': user.username,
        'password': user.password,
        'salt': user.salt,
        'role': user.role,
        'state': user.state,
        'last_login': datetime_to_ISO8601(user.last_login),
        'language': user.language,
        'timezone': user.timezone,
        'password_change_needed': user.password_change_needed,
        'password_change_date': user.password_change_date
    }

    return ret_dict

@transact_ro
def admin_serialize_user(*args):
    return db_admin_serialize_user(*args)


def db_create_step(store, context, steps, language):
    """
    Add the specified steps

    :param store: the store on which perform queries.
    :param context: the context on which register specified steps.
    :param steps: a dictionary containing the new steps.
    :param language: the language of the specified steps.
    """
    for step in steps:
        step['context_id'] = context.id

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

def db_update_steps(store, context, steps, language):
    """
    Update steps

    :param store: the store on which perform queries.
    :param context: the context on which register specified steps.
    :param steps: a dictionary containing the steps to be updated.
    :param language: the language of the specified steps.
    """
    old_steps = store.find(models.Step, models.Step.context_id == context.id)

    indexed_old_steps = {}
    for o in old_steps:
        indexed_old_steps[o.id] = o

    new_steps = []
    for step in steps:
        step['context_id'] = context.id

        fill_localized_keys(step, models.Step.localized_strings, language)

        # check for reuse (needed to keep translations)
        if 'id' in step and step['id'] in indexed_old_steps:
            s = indexed_old_steps[step['id']]
            for field in s.children:
                s.children.remove(field)

            s.update(step)

            del indexed_old_steps[step['id']]
        else:
            s = models.Step(step)

        new_steps.append(s)

        i = 1
        for children in step['children']:
            f = models.Field.get(store, children['id'])
            if not f:
                log.err("Creation error: unexistent field can't be associated")
                raise errors.FieldIdNotFound

            i += 1
            f.y = i

            # remove current step/field fieldgroup/field association
            a_s, _ = get_field_association(store, f.id)
            if a_s is None:
                s.children.add(f)
            elif a_s != s.id:
                disassociate_field(store, f.id)
                s.children.add(f)
            else: # the else condition means a_s == s.id; already associated!
                pass

    for o_id in indexed_old_steps:
        store.remove(indexed_old_steps[o_id])

    for n in new_steps:
        store.add(n)


def admin_serialize_context(store, context, language):
    """
    Serialize the specified context

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the context.
    """
    steps = [anon_serialize_step(store, s, language)
                for s in context.steps.order_by(models.Step.presentation_order)]

    ret_dict = {
        'id': context.id,
        'creation_date': datetime_to_ISO8601(context.creation_date),
        'last_update': datetime_to_ISO8601(context.last_update),
        'receivers': [r.id for r in context.receivers],
        # tip expressed in day, submission in hours
        'tip_timetolive': context.tip_timetolive / (60 * 60 * 24),
        'select_all_receivers': context.select_all_receivers,
        'can_postpone_expiration': context.can_postpone_expiration,
        'can_delete_submission': context.can_delete_submission,
        'maximum_selectable_receivers': context.maximum_selectable_receivers,
        'show_small_cards': context.show_small_cards,
        'show_receivers': context.show_receivers,
        'enable_comments': context.enable_comments,
        'enable_private_messages': context.enable_private_messages,
        'presentation_order': context.presentation_order,
        'show_receivers_in_alphabetical_order': context.show_receivers_in_alphabetical_order,
        'reset_steps': False,
        'steps': steps
    }

    return get_localized_values(ret_dict, context, context.localized_strings, language)


def admin_serialize_receiver(receiver, language):
    """
    Serialize the specified receiver

    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the receiver
    """
    ret_dict = {
        'id': receiver.id,
        'name': receiver.name,
        'creation_date': datetime_to_ISO8601(receiver.creation_date),
        'last_update': datetime_to_ISO8601(receiver.last_update),
        'can_delete_submission': receiver.can_delete_submission,
        'can_postpone_expiration': receiver.can_postpone_expiration,
        'username': receiver.user.username,
        'mail_address': receiver.user.mail_address,
        'ping_mail_address': receiver.ping_mail_address,
        'password': u'',
        'state': receiver.user.state,
        'configuration': receiver.configuration,
        'contexts': [c.id for c in receiver.contexts],
        'pgp_key_info': receiver.pgp_key_info,
        'pgp_key_public': receiver.pgp_key_public,
        'pgp_key_remove': False,
        'pgp_key_fingerprint': receiver.pgp_key_fingerprint,
        'pgp_key_expiration': datetime_to_ISO8601(receiver.pgp_key_expiration),
        'pgp_key_status': receiver.pgp_key_status,
        'tip_notification': receiver.tip_notification,
        'ping_notification': receiver.ping_notification,
        'presentation_order': receiver.presentation_order,
        'language': receiver.user.language,
        'timezone': receiver.user.timezone,
        'tip_expiration_threshold': receiver.tip_expiration_threshold,
        'password_change_needed': receiver.user.password_change_needed,
    }

    return get_localized_values(ret_dict, receiver, receiver.localized_strings, language)


def db_update_node(store, request, wizard_done, language):
    """
    Update and serialize the node infos

    :param store: the store on which perform queries.
    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the node
    """
    node = store.find(models.Node).one()

    fill_localized_keys(request, models.Node.localized_strings, language)

    admin = store.find(models.User, (models.User.username == unicode('admin'))).one()

    admin.mail_address = request['email']
    admin.language = request['admin_language']
    admin.timezone = request['admin_timezone']

    password = request.get('password', None)
    old_password = request.get('old_password', None)

    if password and old_password and len(password) and len(old_password):
        admin.password = security.change_password(admin.password,
                                    old_password, password, admin.salt)

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

    if wizard_done:
        node.wizard_done = True

    try:
        node.update(request)
    except DatabaseError as dberror:
        log.err("Unable to update Node: %s" % dberror)
        raise errors.InvalidInputFormat(dberror)

    node.last_update = datetime_now()

    db_update_memory_variables(store)

    return db_admin_serialize_node(store, language)


@transact
def update_node(*args):
    return db_update_node(*args)


@transact_ro
def get_context_list(store, language):
    """
    Returns the context list.

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the contexts.
    """
    contexts = store.find(models.Context).order_by(models.Context.presentation_order)
    context_list = []

    for context in contexts:
        context_list.append(admin_serialize_context(store, context, language))

    return context_list


def acquire_context_timetolive(timetolive):
    if timetolive <= 0:
        raise errors.InvalidTipTimeToLive()

    return timetolive * (24 * 60 * 60)


def field_is_present(store, field):
    result = store.find(models.Field,
                        models.Field.label == field['label'],
                        models.Field.description == field['description'],
                        models.Field.hint == field['hint'],
                        models.Field.multi_entry == field['multi_entry'],
                        models.Field.type == field['type'],
                        models.Field.preview == field['preview'])

    return result.count() > 0


def db_setup_default_steps(store, context):
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
                o.presentation_order = n_o
                f.options.add(o)
                n_o += 1
            f.step_id = s.id
            s.children.add(f)
        s.context_id = context.id
        s.presentation_order = n_s
        context.steps.add(s)
        n_s += 1


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

    # tip_timetolive to be converted in seconds since hours and days
    context.tip_timetolive = acquire_context_timetolive(int(request['tip_timetolive']))

    c = store.add(context)

    for receiver_id in receivers:
        receiver = models.Receiver.get(store, receiver_id)
        if not receiver:
            log.err("Creation error: unexistent context can't be associated")
            raise errors.ReceiverIdNotFound
        c.receivers.add(receiver)

    if steps:
        db_create_step(store, context, steps, language)
    else:
        db_setup_default_steps(store, context)

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

    context.tip_timetolive = acquire_context_timetolive(int(request['tip_timetolive']))

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

    if request['reset_steps']:
        db_update_steps(store, context, [], language)
        db_setup_default_steps(store, context)
    else:
        db_update_steps(store, context, steps, language)

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

    receivers = store.find(models.Receiver).order_by(models.Receiver.presentation_order)

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

    password = request['password']
    if len(password) and password != GLSetting.default_password:
        security.check_password_format(password)
    else:
        password = GLSetting.default_password

    receiver_salt = security.get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    receiver_password = security.hash_password(password, receiver_salt)

    # ping_mail_address is duplicated at creation time from mail_address
    request.update({'ping_mail_address': request['mail_address']})

    receiver = models.Receiver(request)

    receiver_user_dict = {
        'username': uuid4(),
        'password': receiver_password,
        'salt': receiver_salt,
        'role': u'receiver',
        'state': u'enabled',
        'language': u'en',
        'timezone': 0,
        'password_change_needed': True,
        'mail_address': request['mail_address']
    }

    receiver_user = models.User(receiver_user_dict)

    # The various options related in manage PGP keys are used here.
    pgp_options_parse(receiver, request)

    # Set receiver.id = receiver.user.username = receiver.user.id
    receiver.id = receiver_user.username = receiver_user.id

    store.add(receiver_user)
    store.add(receiver)

    create_random_receiver_portrait(receiver.id)

    contexts = request.get('contexts', [])
    for context_id in contexts:
        context = models.Context.get(store, context_id)
        if not context:
            log.err("Creation error: invalid Context can't be associated")
            raise errors.ContextIdNotFound
        context.receivers.add(receiver)

    log.debug("Created receiver %s" % receiver.user.username)

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

    receiver.user.state = request['state']
    receiver.user.password_change_needed = request['password_change_needed']
    receiver.user.mail_address = request['mail_address']

    # The various options related in manage PGP keys are used here.
    pgp_options_parse(receiver, request)

    receiver.user.language = request.get('language', GLSetting.memory_copy.language)
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
        raise errors.ReceiverIdNotFound

    portrait = os.path.join(GLSetting.static_path, "%s.png" % receiver_id)

    if os.path.exists(portrait):
        os.remove(portrait)

    store.remove(receiver.user)


def pgp_options_parse(receiver, request):
    """
    This is called in a @transact, when receiver update prefs and
    when admin configure a new key (at the moment, Admin GUI do not
    permit to sets preferences, but still the same function is
    used.

    @param receiver: the Storm object
    @param request: the Dict receiver by the Internets
    @return: None

    This function is called in create_recever and update_receiver
    and is used to manage the PGP options forced by the administrator

    This is needed also because no one of these fields are
    *enforced* by unicode_keys or bool_keys in models.Receiver

    PGP management, here are check'd these actions:
    1) Proposed a new PGP key, is imported to check validity, and
       stored in Storm DB if not error raise
    2) Removal of the present key

    Further improvement: update the keys using keyserver
    """

    new_pgp_key = request.get('pgp_key_public', None)
    remove_key = request.get('pgp_key_remove', False)

    # the default
    receiver.pgp_key_status = u'disabled'

    if remove_key:
        log.debug("User %s %s request to remove PGP key (%s)" %
                  (receiver.name, receiver.user.username, receiver.pgp_key_fingerprint))

        # In all the cases below, the key is marked disabled as request
        receiver.pgp_key_status = u'disabled'
        receiver.pgp_key_info = None
        receiver.pgp_key_public = None
        receiver.pgp_key_fingerprint = None
        receiver.pgp_key_expiration = datetime_null()

    if new_pgp_key:
        gnob = GLBPGP()

        try:
            result = gnob.load_key(new_pgp_key)

            log.debug("PGP Key imported: %s" % result['fingerprint'])

            receiver.pgp_key_status = u'enabled'
            receiver.pgp_key_info = result['info']
            receiver.pgp_key_public = new_pgp_key
            receiver.pgp_key_fingerprint = result['fingerprint']
            receiver.pgp_key_expiration = result['expiration']

        except:
            raise

        finally:
            # the finally statement is always called also if
            # except contains a return or a raise
            gnob.destroy_environment()


# ---------------------------------
# Below starts the Cyclone handlers
# ---------------------------------


class NodeInstance(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Get the node infos.

        Parameters: None
        Response: AdminNodeDesc
        """
        node_description = yield admin_serialize_node(self.request.language)
        self.set_status(200)
        self.finish(node_description)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self):
        """
        Update the node infos.

        Request: AdminNodeDesc
        Response: AdminNodeDesc
        Errors: InvalidInputFormat
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminNodeDesc)

        node_description = yield update_node(request, True, self.request.language)
        GLApiCache.invalidate()

        self.set_status(202) # Updated
        self.finish(node_description)


class ContextsCollection(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return all the contexts.

        Parameters: None
        Response: adminContextList
        Errors: None
        """
        response = yield get_context_list(self.request.language)

        self.set_status(200)
        self.finish(response)


class ContextCreate(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new context.

        Request: AdminContextDesc
        Response: AdminContextDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminContextDesc)

        response = yield create_context(request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(201) # Created
        self.finish(response)


class ContextInstance(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, context_id):
        """
        Get the specified context.

        Parameters: context_id
        Response: AdminContextDesc
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
        Update the specified context.

        Parameters: context_id
        Request: AdminContextDesc
        Response: AdminContextDesc
        Errors: InvalidInputFormat, ContextIdNotFound, ReceiverIdNotFound

        Updates the specified context.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminContextDesc)

        response = yield update_context(context_id, request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, context_id):
        """
        Delete the specified context.

        Request: AdminContextDesc
        Response: None
        Errors: InvalidInputFormat, ContextIdNotFound
        """
        yield delete_context(context_id)
        GLApiCache.invalidate()

        self.set_status(200) # Ok and return no content
        self.finish()


class ReceiversCollection(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return all the receivers.

        Parameters: None
        Response: adminReceiverList
        Errors: None
        """
        response = yield get_receiver_list(self.request.language)

        self.set_status(200)
        self.finish(response)


class ReceiverCreate(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Get the specified receiver.

        Request: AdminReceiverDesc
        Response: AdminReceiverDesc
        Errors: InvalidInputFormat, ContextIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminReceiverDesc)

        response = yield create_receiver(request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(201) # Created
        self.finish(response)


class ReceiverInstance(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, receiver_id):
        """
        Get the specified receiver.

        Parameters: receiver_id
        Response: AdminReceiverDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        response = yield get_receiver(receiver_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, receiver_id):
        """
        Update the specified receiver.

        Parameters: receiver_id
        Request: AdminReceiverDesc
        Response: AdminReceiverDesc
        Errors: InvalidInputFormat, ReceiverIdNotFound, ContextId
        """
        request = self.validate_message(self.request.body, requests.AdminReceiverDesc)

        response = yield update_receiver(receiver_id, request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(201)
        self.finish(response)

    @inlineCallbacks
    @transport_security_check('admin')
    @authenticated('admin')
    def delete(self, receiver_id):
        """
        Delete the specified receiver.

        Parameters: receiver_id
        Request: None
        Response: None
        Errors: InvalidInputFormat, ReceiverIdNotFound
        """
        yield delete_receiver(receiver_id)

        # get the updated list of receivers, and update the cache
        GLApiCache.invalidate()

        self.set_status(200) # OK and return not content
        self.finish()
