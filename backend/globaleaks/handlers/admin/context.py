# -*- coding: UTF-8
#
#   /admin/context
#   *****
# Implementation of the code executed on handler /admin/context
#
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.admin.field import db_import_fields
from globaleaks.handlers.node import anon_serialize_step
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.third_party import rstr
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now, datetime_null, datetime_to_ISO8601, uuid4


def admin_serialize_context(store, context, language):
    """
    Serialize the specified context

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the context.
    """
    steps = [anon_serialize_step(store, s, language) for s in context.steps]

    ret_dict = {
        'id': context.id,
        'receivers': [r.id for r in context.receivers],
        # tip expressed in day, submission in hours
        'tip_timetolive': context.tip_timetolive / (60 * 60 * 24),
        'select_all_receivers': context.select_all_receivers,
        'maximum_selectable_receivers': context.maximum_selectable_receivers,
        'show_context': context.show_context,
        'show_receivers': context.show_receivers,
        'show_small_cards': context.show_small_cards,
        'enable_comments': context.enable_comments,
        'enable_messages': context.enable_messages,
        'enable_two_way_communication': context.enable_two_way_communication,
        'enable_attachments': context.enable_attachments,
        'presentation_order': context.presentation_order,
        'show_receivers_in_alphabetical_order': context.show_receivers_in_alphabetical_order,
        'steps_arrangement': context.steps_arrangement,
        'reset_steps': False,
        'steps': steps
    }

    return get_localized_values(ret_dict, context, context.localized_strings, language)


@transact_ro
def get_context_list(store, language):
    """
    Returns the context list.

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the contexts.
    """
    contexts = store.find(models.Context)

    return [admin_serialize_context(store, context, language) for context in contexts]


def acquire_context_timetolive(timetolive):
    if timetolive <= 0:
        raise errors.InvalidTipTimeToLive()

    return timetolive * (24 * 60 * 60)


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

    # context steps are initialized with the application default
    db_setup_default_steps(store, c.id)

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
        (dict) the questionnaire associated with the context with the specified id.
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
def db_reset_steps(store, context_id):
    store.find(models.Step, models.Step.context_id == context_id).remove()


def db_setup_default_steps(store, context_id):
    appdata = store.find(models.ApplicationData).one()
    steps = copy.deepcopy(appdata.fields)
    for step in steps:
        f_children = copy.deepcopy(step['children'])
        del step['children']
        s = models.db_forge_obj(store, models.Step, step)
        db_import_fields(store, s, None, f_children)
        s.context_id = context_id


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

    context.update(request)

    if request['reset_steps']:
        db_reset_steps(store, context.id)
        db_setup_default_steps(store, context.id)

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
