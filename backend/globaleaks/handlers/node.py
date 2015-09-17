# -*- coding: UTF-8
# node
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.settings import transact_ro, GLSettings
from globaleaks.rest.apicache import GLApiCache

@transact_ro
def anon_serialize_ahmia(store, language):
    """
    Serialize Ahmia.fi descriptor.
    """
    node = store.find(models.Node).one()

    mo = Rosetta(node.localized_strings)
    mo.acquire_storm_object(node)

    ret_dict = {
        'title': node.name,
        'description': mo.dump_localized_key('description', language),
        'keywords': '%s (GlobaLeaks instance)' % node.name,
        'relation': node.public_site,
        'language': node.default_language,
        'contactInformation': u'',
        'type': 'GlobaLeaks'
    }

    return ret_dict


@transact_ro
def anon_serialize_node(store, language):
    """
    Serialize node infos.
    """
    node = store.find(models.Node).one()

    # Contexts and Receivers relationship
    configured = store.find(models.ReceiverContext).count() > 0

    ret_dict = {
        'name': node.name,
        'hidden_service': node.hidden_service,
        'public_site': node.public_site,
        'email': u'',
        'languages_enabled': node.languages_enabled,
        'languages_supported': LANGUAGES_SUPPORTED,
        'default_language': node.default_language,
        'default_timezone': node.default_timezone,
        'maximum_namesize': node.maximum_namesize,
        'maximum_textsize': node.maximum_textsize,
        'maximum_filesize': node.maximum_filesize,
        'tor2web_admin': GLSettings.memory_copy.tor2web_admin,
        'tor2web_custodian': GLSettings.memory_copy.tor2web_custodian,
        'tor2web_whistleblower': GLSettings.memory_copy.tor2web_whistleblower,
        'tor2web_receiver': GLSettings.memory_copy.tor2web_receiver,
        'tor2web_unauth': GLSettings.memory_copy.tor2web_unauth,
        'submission_minimum_delay': 0 if GLSettings.devel_mode else GLSettings.memory_copy.submission_minimum_delay,
        'submission_maximum_ttl': GLSettings.memory_copy.submission_maximum_ttl,
        'ahmia': node.ahmia,
        'can_postpone_expiration': node.can_postpone_expiration,
        'can_delete_submission': node.can_delete_submission,
        'wizard_done': node.wizard_done,
        'allow_unencrypted': node.allow_unencrypted,
        'allow_iframes_inclusion': node.allow_iframes_inclusion,
        'configured': configured,
        'password': u'',
        'old_password': u'',
        'disable_privacy_badge': node.disable_privacy_badge,
        'disable_security_awareness_badge': node.disable_security_awareness_badge,
        'disable_security_awareness_questions': node.disable_security_awareness_questions,
        'disable_key_code_hint': node.disable_key_code_hint,
        'simplified_login': node.simplified_login,
        'enable_custom_privacy_badge': node.enable_custom_privacy_badge,
        'landing_page': node.landing_page,
        'show_contexts_in_alphabetical_order': node.show_contexts_in_alphabetical_order,
        'accept_submissions': GLSettings.memory_copy.accept_submissions,
        'graph_captcha': node.graph_captcha,
        'human_captcha': node.human_captcha,
        'proof_of_work': node.proof_of_work
    }

    return get_localized_values(ret_dict, node, node.localized_strings, language)


def anon_serialize_context(store, context, language):
    """
    Serialize context description

    @param context: a valid Storm object
    @return: a dict describing the contexts available for submission,
        (e.g. checks if almost one receiver is associated)
    """
    receivers = [r.id for r in context.receivers]
    if not len(receivers):
        return None

    steps = [anon_serialize_step(store, s, language) for s in context.steps]

    ret_dict = {
        'id': context.id,
        'tip_timetolive': context.tip_timetolive,
        'description': context.description,
        'select_all_receivers': context.select_all_receivers,
        'maximum_selectable_receivers': context.maximum_selectable_receivers,
        'show_small_cards': context.show_small_cards,
        'show_receivers': context.show_receivers,
        'enable_comments': context.enable_comments,
        'enable_messages': context.enable_messages,
        'enable_two_way_communication': context.enable_two_way_communication,
        'enable_attachments': context.enable_attachments,
        'presentation_order': context.presentation_order,
        'show_receivers_in_alphabetical_order': context.show_receivers_in_alphabetical_order,
        'steps_arrangement': context.steps_arrangement,
        'receivers': receivers,
        'steps': steps
    }

    return get_localized_values(ret_dict, context, context.localized_strings, language)


def anon_serialize_option(option, language):
    """
    Serialize a field option, localizing its content depending on the language.

    :param option: the field option object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    ret_dict = {
        'id': option.id,
        'presentation_order': option.presentation_order,
        'score_points': option.score_points,
        'activated_fields': [field.id for field in option.activated_fields],
        'activated_steps': [step.id for step in option.activated_steps]
    }

    return get_localized_values(ret_dict, option, option.localized_strings, language)


def anon_serialize_field(store, field, language):
    """
    Serialize a field, localizing its content depending on the language.

    :param field: the field object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """

    # naif likes if we add reference links
    # this code is inspired by:
    #  - https://www.youtube.com/watch?v=KtNsUgKgj9g

    if field.template:
        f_to_serialize = field.template
    else:
        f_to_serialize = field

    options = [anon_serialize_option(o, language) for o in f_to_serialize.options]

    sf = store.find(models.StepField, models.StepField.field_id == field.id).one()
    step_id = sf.step_id if sf else ''

    ff = store.find(models.FieldField, models.FieldField.child_id == field.id).one()
    fieldgroup_id = ff.parent_id if ff else ''

    fields = []
    for f in f_to_serialize.children:
        fields.append(anon_serialize_field(store, f, language))

    attrs = {}
    for attr in store.find(models.FieldAttr, models.FieldAttr.field_id == f_to_serialize.id):
        attrs[attr.name] = {}
        attrs[attr.name]['type'] = attr.type
        attrs[attr.name]['value'] = attr.value
        if attr.type == u'localized':
            get_localized_values(attrs[attr.name], attrs[attr.name], ['value'], language)

    activated_by_options = [activation.option_id for activation in field.activated_by_options]

    ret_dict = {
        'id': field.id,
        'type': f_to_serialize.type,
        'is_template': field.is_template,
        'template_id': field.template.id if field.template else '',
        'step_id': step_id,
        'fieldgroup_id': fieldgroup_id,
        'multi_entry': field.multi_entry,
        'required': field.required,
        'preview': field.preview,
        'stats_enabled': field.stats_enabled,
        'attrs': attrs,
        'x': field.x,
        'y': field.y,
        'width': field.width,
        'activated_by_score': field.activated_by_score,
        'activated_by_options': activated_by_options,
        'options': options,
        'children': fields
    }

    return get_localized_values(ret_dict, f_to_serialize, field.localized_strings, language)


def anon_serialize_step(store, step, language):
    """
    Serialize a step, localizing its content depending on the language.

    :param step: the step to be serialized.
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    fields = []
    for f in step.children:
        fields.append(anon_serialize_field(store, f, language))

    ret_dict = {
        'id': step.id,
        'context_id': step.context.id,
        'presentation_order': step.presentation_order,
        'children': fields
    }

    return get_localized_values(ret_dict, step, step.localized_strings, language)


def anon_serialize_receiver(receiver, language):
    """
    Serialize a receiver description

    :param receiver: the receiver to be serialized
    :param language: the language in which to localize data
    :return: a serializtion of the object
    """
    ret_dict = {
        'name': receiver.user.name,
        'id': receiver.id,
        'username': receiver.user.username,
        'state': receiver.user.state,
        'configuration': receiver.configuration,
        'presentation_order': receiver.presentation_order,
        'pgp_key_status': receiver.user.pgp_key_status,
        'contexts': [c.id for c in receiver.contexts]
    }

    # description and eventually other localized strings should be taken from user model
    get_localized_values(ret_dict, receiver.user, ['description'], language)

    return get_localized_values(ret_dict, receiver, receiver.localized_strings, language)


@transact_ro
def get_public_context_list(store, language):
    context_list = []
    contexts = store.find(models.Context)

    for context in contexts:
        context_desc = anon_serialize_context(store, context, language)
        # context not yet ready for submission return None
        if context_desc:
            context_list.append(context_desc)

    return context_list


@transact_ro
def get_public_receiver_list(store, language):
    receiver_list = []
    receivers = store.find(models.Receiver)

    for receiver in receivers:
        if receiver.user.state == u'disabled':
            continue

        receiver_desc = anon_serialize_receiver(receiver, language)
        # receiver not yet ready for submission return None
        if receiver_desc:
            receiver_list.append(receiver_desc)

    return receiver_list


class NodeInstance(BaseHandler):
    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self):
        """
        Get the node infos.
        """
        ret = yield GLApiCache.get('node', self.request.language,
                                   anon_serialize_node, self.request.language)

        ret['custom_homepage'] = os.path.isfile(os.path.join(GLSettings.static_path,
                                                             "custom_homepage.html"))

        self.finish(ret)


class AhmiaDescriptionHandler(BaseHandler):
    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self):
        """
        Get the Ahmia.fi descriptor
        """
        node_info = yield GLApiCache.get('node', self.request.language,
                                         anon_serialize_node, self.request.language)

        if node_info['ahmia']:
            ret = yield GLApiCache.get('ahmia', self.request.language,
                                       anon_serialize_ahmia, self.request.language)

            self.finish(ret)
        else:  # in case of disabled option we return 404
            self.set_status(404)
            self.finish()


class ContextsCollection(BaseHandler):
    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self):
        """
        Get all the contexts.
        """
        ret = yield GLApiCache.get('contexts', self.request.language,
                                   get_public_context_list, self.request.language)
        self.finish(ret)


class ReceiversCollection(BaseHandler):
    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self):
        """
        Gets all the receivers.
        """
        ret = yield GLApiCache.get('receivers', self.request.language,
                                   get_public_receiver_list, self.request.language)
        self.finish(ret)
