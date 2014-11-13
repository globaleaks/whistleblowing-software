# -*- coding: UTF-8
#   node
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.utils.utility import datetime_to_ISO8601
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.settings import transact_ro, GLSetting, stats_counter
from globaleaks.handlers.base import BaseHandler, GLApiCache
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks import models, LANGUAGES_SUPPORTED

def get_field_option_localized_keys(field_type):
    localized_keys = []
    if field_type == 'checkbox' or field_type =='selectbox':
        localized_keys = ['name']
    elif field_type == 'tos':
        localized_keys = ['clause', 'agreement_statement']

    return localized_keys

@transact_ro
def anon_serialize_ahmia(store, language=GLSetting.memory_copy.default_language):
    """
    Request reaches only if ahmia is enabled
    """
    node = store.find(models.Node).one()

    mo = Rosetta(node.localized_strings)
    mo.acquire_storm_object(node)

    ret_dict = {
        "title": node.name,
        "description": mo.dump_localized_attr('description', language),

        # TODO support tags/keyword in Node.
        "keywords": "%s (GlobaLeaks instance)" % node.name,
        "relation": node.public_site,

        # TODO ask Ahmia to support a list of languages
        "language": node.default_language,

        # TODO say to the admin that its email will be public
        "contactInformation": u'',
        "type": "GlobaLeaks"
    }

    return ret_dict

@transact_ro
def anon_serialize_node(store, language=GLSetting.memory_copy.default_language):
    node = store.find(models.Node).one()

    # Contexts and Receivers relationship
    associated = store.find(models.ReceiverContext).count()

    custom_homepage = False

    try:
        custom_homepage = os.path.isfile(os.path.join(GLSetting.static_path, "custom_homepage.html"))
    except:
        pass

    ret_dict = {
      'name': node.name,
      'hidden_service': node.hidden_service,
      'public_site': node.public_site,
      'email': node.email,
      'languages_enabled': node.languages_enabled,
      'languages_supported': LANGUAGES_SUPPORTED,
      'default_language' : node.default_language,
      # extended settings info:
      'maximum_namesize': node.maximum_namesize,
      'maximum_textsize': node.maximum_textsize,
      'maximum_filesize': node.maximum_filesize,
      # public serialization use GLSetting memory var, and
      # not the real one, because needs to bypass
      # Tor2Web unsafe deny default settings
      'tor2web_admin': GLSetting.memory_copy.tor2web_admin,
      'tor2web_submission': GLSetting.memory_copy.tor2web_submission,
      'tor2web_receiver': GLSetting.memory_copy.tor2web_receiver,
      'tor2web_unauth': GLSetting.memory_copy.tor2web_unauth,
      'ahmia': node.ahmia,
      'postpone_superpower': node.postpone_superpower,
      'can_delete_submission': node.can_delete_submission,
      'wizard_done': node.wizard_done,
      'anomaly_checks': node.anomaly_checks,
      'allow_unencrypted': node.allow_unencrypted,
      'x_frame_options_mode': node.x_frame_options_mode,
      'x_frame_options_allow_from': node.x_frame_options_allow_from,
      'receipt_regexp': node.receipt_regexp,
      'configured': True if associated else False,
      'password': u"",
      'old_password': u"",
      'custom_homepage': custom_homepage,
      'disable_privacy_badge': node.disable_privacy_badge,
      'disable_security_awareness_badge': node.disable_security_awareness_badge,
      'disable_security_awareness_questions': node.disable_security_awareness_questions
    }

    return get_localized_values(ret_dict, node, node.localized_strings, language)

def anon_serialize_context(store, context, language=GLSetting.memory_copy.default_language):
    """
    @param context: a valid Storm object
    @return: a dict describing the contexts available for submission,
        (e.g. checks if almost one receiver is associated)
    """

    receivers = [r.id for r in context.receivers]
    if not len(receivers):
        return None

    steps = [ anon_serialize_step(store, s, language)
              for s in context.steps.order_by(models.Step.number) ]
    ret_dict = {
        "id": context.id,
        "escalation_threshold": 0,
        "file_max_download": context.file_max_download,
        "file_required": context.file_required,
        "selectable_receiver": context.selectable_receiver,
        "tip_max_access": context.tip_max_access,
        "tip_timetolive": context.tip_timetolive,
        "submission_introduction": u'NYI', # unicode(context.submission_introduction), # optlang
        "submission_disclaimer": u'NYI', # unicode(context.submission_disclaimer), # optlang
        "select_all_receivers": context.select_all_receivers,
        "maximum_selectable_receivers": context.maximum_selectable_receivers,
        'require_pgp': context.require_pgp,
        "show_small_cards": context.show_small_cards,
        "show_receivers": context.show_receivers,
        "enable_private_messages": context.enable_private_messages,
        "presentation_order": context.presentation_order,
        "receivers": receivers,
        "steps": steps
    }

    return get_localized_values(ret_dict, context, context.localized_strings, language)

def anon_serialize_option(option, field_type, language):
    """
    Serialize a field option, localizing its content depending on the language.

    :param option: the field option object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """

    ret_dict = {
        'id': option.id,
        'attrs': {}
    }

    keys = get_field_option_localized_keys(field_type)
    
    get_localized_values(ret_dict['attrs'], option.attrs, keys, language)

    return ret_dict

def anon_serialize_field(store, field, language):
    """
    Serialize a field, localizing its content depending on the language.

    :param field: the field object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """

    options = [ anon_serialize_option(o, field.type, language) for o in field.options ]

    sf = store.find(models.StepField, models.StepField.field_id == field.id).one()
    step_id = sf.step_id if sf else ''

    ff = store.find(models.FieldField, models.FieldField.child_id == field.id).one()
    fieldgroup_id = ff.id if ff else ''

    ret_dict = {
        'id': field.id,
        'step_id': step_id,
        'fieldgroup_id': fieldgroup_id,
        'multi_entry': field.multi_entry,
        'required': field.required,
        'preview': False,
        'stats_enabled': field.stats_enabled,
        'type': field.type,
        'x': field.x,
        'y': field.y,
        'options': options,
        'children': [f.id for f in field.children],
    }

    return get_localized_values(ret_dict, field, field.localized_strings, language)

def anon_serialize_step(store, step, language):
    """
    Serialize a step, localizing its content depending on the language.

    :param step: the step object to be serialized.
    :param language: the language in which to localize data
    :return: a serialization of the object
    """

    fields = dict()
    for f in step.children.order_by(models.Field.y):
        fields[f.id] = anon_serialize_field(store, f, language)

    ret_dict = {
        'id': step.id,
        'children': fields
    }

    return get_localized_values(ret_dict, step, step.localized_strings, language)

def anon_serialize_receiver(receiver, language=GLSetting.memory_copy.default_language):
    """
    @param receiver: a valid Storm object
    @return: a dict describing the receivers available in the node
        (e.g. checks if almost one context is associated, or, in
         node where GPG encryption is enforced, that a valid key is registered)
    """

    contexts = [c.id for c in receiver.contexts]
    if not len(contexts):
        return None

    ret_dict = {
        "creation_date": datetime_to_ISO8601(receiver.creation_date),
        "update_date": datetime_to_ISO8601(receiver.last_update),
        "name": receiver.name,
        "id": receiver.id,
        "receiver_level": receiver.receiver_level,
        "tags": receiver.tags,
        "presentation_order": receiver.presentation_order,
        "gpg_key_status": receiver.gpg_key_status,
        "contexts": contexts
    }

    return get_localized_values(ret_dict, receiver, receiver.localized_strings, language)


class InfoCollection(BaseHandler):
    """
    U1
    Returns information on the GlobaLeaks node. This includes submission
    parameters (contexts description, fields, public receiver list).
    Contains System-wide properties.
    """

    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicNodeDesc
        Errors: NodeNotFound
        """
        stats_counter('anon_requests')
        ret = yield GLApiCache.get('node', self.request.language,
                                   anon_serialize_node, self.request.language)
        self.finish(ret)


class AhmiaDescriptionHandler(BaseHandler):
    """
    Description of Ahmia 'protocol' is in:
    https://ahmia.fi/documentation/
    and we're supporting the Hidden Service description proposal from:
    https://ahmia.fi/documentation/descriptionProposal/
    """

    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):

        stats_counter('anon_requests')

        node_info = yield GLApiCache.get('node', self.request.language,
                                         anon_serialize_node, self.request.language)

        if node_info['ahmia']:
            ret = yield GLApiCache.get('ahmia', self.request.language,
                                   anon_serialize_ahmia, self.request.language)

            self.finish(ret)
        else: # in case of disabled option we return 404
            self.set_status(404)
            self.finish()


@transact_ro
def get_public_context_list(store, default_lang):
    context_list = []
    contexts = store.find(models.Context)

    for context in contexts:
        context_desc = anon_serialize_context(store, context, default_lang)
        # context not yet ready for submission return None
        if context_desc:
            context_list.append(context_desc)

    return context_list


class ContextsCollection(BaseHandler):
    """
    Return the public list of contexts, those information are shown in client
    and would be memorized in a third party indexer service. This is way some dates
    are returned within.
    """
    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicContextList
        Errors: None
        """

        stats_counter('anon_requests')
        ret = yield GLApiCache.get('contexts', self.request.language,
                                   get_public_context_list, self.request.language)
        self.finish(ret)

@transact_ro
def get_public_field_list(store, language):
    """
    :return: the current field list serialized.
    :rtype: dict
    """
    return [anon_serialize_field(store, f, language) for f in store.find(models.Field)]

class FieldsCollection(BaseHandler):
    """
    /admin/fields
    """
    @transport_security_check('unauth')
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Return a list of all the fields available.

        Parameters: None
        Response: adminFieldList
        Errors: None
        """
        ret = yield get_public_field_list(self.request.language)
        self.set_status(200)
        self.finish(ret)

@transact_ro
def get_public_receiver_list(store, default_lang):
    receiver_list = []
    receivers = store.find(models.Receiver)

    for receiver in receivers:
        receiver_desc = anon_serialize_receiver(receiver, default_lang)
        # receiver not yet ready for submission return None
        if receiver_desc:
            receiver_list.append(receiver_desc)

    return receiver_list

class ReceiversCollection(BaseHandler):
    """
    Return the description of all the receivers visible from the outside.
    """

    @transport_security_check("unauth")
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: publicReceiverList
        Errors: None
        """

        stats_counter('anon_requests')
        ret = yield GLApiCache.get('receivers', self.request.language,
                                   get_public_receiver_list, self.request.language)
        self.finish(ret)
