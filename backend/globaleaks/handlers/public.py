# -*- coding: UTF-8
# public
#   ****
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.
import copy
from storm.expr import In, Select

from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.handlers.admin.files import db_get_file
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import l10n
from globaleaks.models.config import NodeFactory
from globaleaks.models.l10n import NodeL10NFactory
from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.utils.sets import merge_dicts
from globaleaks.utils.structures import get_localized_values


def db_prepare_contexts_serialization(store, contexts):
    data = {'imgs': {}, 'receivers': {}}

    contexts_ids = []
    img_ids = []

    for c in contexts:
        contexts_ids.append(c.id)
        if c.img_id is not None:
            img_ids.append(c.img_id)

    for o in store.find(models.File, In(models.File.id, img_ids)):
        data['imgs'][o.id] = o.data

    for o in store.find(models.ReceiverContext, In(models.ReceiverContext.context_id, contexts_ids)):
        if o.context_id not in data['receivers']:
            data['receivers'][o.context_id] = []
        data['receivers'][o.context_id].append(o.receiver_id)

    return data


def db_prepare_receivers_serialization(store, receivers):
    data = {'users': {}, 'imgs': {}, 'contexts': {}}

    receivers_ids = []
    img_ids = []

    for r in receivers:
        receivers_ids.append(r.id)

    for o in store.find(models.User, In(models.User.id, receivers_ids)):
        data['users'][o.id] = o
        img_ids.append(o.img_id)

    for o in store.find(models.File, In(models.File.id, img_ids)):
        data['imgs'][o.id] = o.data

    for o in store.find(models.ReceiverContext, In(models.ReceiverContext.receiver_id, receivers_ids)):
        if o.receiver_id not in data['contexts']:
            data['contexts'][o.receiver_id] = []
        data['contexts'][o.receiver_id].append(o.context_id)

    return data


def db_prepare_fields_serialization(store, fields):
    ret = {
        'fields': {},
        'attrs': {},
        'options': {},
        'triggers': {}
    }

    fields_ids = []
    for f in fields:
        fields_ids.append(f.id)
        if f.template_id is not None:
            fields_ids.append(f.template_id)

    tmp = copy.deepcopy(fields_ids)
    while tmp:
        fs = store.find(models.Field, In(models.Field.fieldgroup_id, tmp))

        tmp = []
        for f in fs:
            tmp.append(f.id)
            if f.template_id is not None:
                tmp.append(f.template_id)

            if f.fieldgroup_id not in ret['fields']:
                ret['fields'][f.fieldgroup_id] = []
            ret['fields'][f.fieldgroup_id].append(f)

        fields_ids.extend(tmp)

    objs = store.find(models.FieldAttr, In(models.FieldAttr.field_id, fields_ids))
    for obj in objs:
        if obj.field_id not in ret['attrs']:
            ret['attrs'][obj.field_id] = []
        ret['attrs'][obj.field_id].append(obj)

    objs = store.find(models.FieldOption, In(models.FieldOption.field_id, fields_ids))
    for obj in objs:
        if obj.field_id not in ret['options']:
            ret['options'][obj.field_id] = []
        ret['options'][obj.field_id].append(obj)

    objs = store.find(models.FieldOption, In(models.FieldOption.trigger_field, fields_ids))
    for obj in objs:
        if obj.field_id not in ret['triggers']:
            ret['triggers'][obj.field_id] = []
        ret['triggers'][obj.field_id].append(obj)

    return ret


def db_serialize_node(store, language):
    """
    Serialize node info.
    """
    # Contexts and Receivers relationship
    configured = store.find(models.ReceiverContext).count() > 0

    ro_node = NodeFactory(store).public_export()

    misc_dict = {
        'languages_enabled': l10n.EnabledLanguage.list(store),
        'languages_supported': LANGUAGES_SUPPORTED,
        'configured': configured,
        'accept_submissions': GLSettings.accept_submissions,
        'logo': db_get_file(store, u'logo'),
        'favicon': db_get_file(store, u'favicon'),
        'css': db_get_file(store, u'css'),
        'homepage': db_get_file(store, u'homepage'),
        'script': db_get_file(store, u'script')
    }

    l10n_dict = NodeL10NFactory(store).localized_dict(language)

    return merge_dicts(ro_node, l10n_dict, misc_dict)


@transact
def serialize_node(store, language):
    return db_serialize_node(store, language)


def serialize_context(store, context, language, data=None):
    """
    Serialize context description

    @param context: a valid Storm object
    @return: a dict describing the contexts available for submission,
        (e.g. checks if almost one receiver is associated)
    """
    ret_dict = {
        'id': context.id,
        'presentation_order': context.presentation_order,
        'tip_timetolive': context.tip_timetolive,
        'select_all_receivers': context.select_all_receivers,
        'maximum_selectable_receivers': context.maximum_selectable_receivers,
        'show_context': context.show_context,
        'show_recipients_details': context.show_recipients_details,
        'allow_recipients_selection': context.allow_recipients_selection,
        'show_small_receiver_cards': context.show_small_receiver_cards,
        'enable_comments': context.enable_comments,
        'enable_messages': context.enable_messages,
        'enable_two_way_comments': context.enable_two_way_comments,
        'enable_two_way_messages': context.enable_two_way_messages,
        'enable_attachments': context.enable_attachments,
        'enable_rc_to_wb_files': context.enable_rc_to_wb_files,
        'show_receivers_in_alphabetical_order': context.show_receivers_in_alphabetical_order,
        'questionnaire_id': context.questionnaire_id,
        'receivers': data['receivers'].get(context.id, []),
        'picture': data['imgs'].get(context.img_id, '')
    }

    return get_localized_values(ret_dict, context, context.localized_keys, language)


def serialize_questionnaire(store, questionnaire, language):
    """
    Serialize the specified questionnaire

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the questionnaire.
    """
    steps = store.find(models.Step, questionnaire_id=questionnaire.id)

    ret_dict = {
        'id': questionnaire.id,
        'editable': questionnaire.editable,
        'name': questionnaire.name,
        'show_steps_navigation_bar': questionnaire.show_steps_navigation_bar,
        'steps_navigation_requires_completion': questionnaire.steps_navigation_requires_completion,
        'steps': [serialize_step(store, s, language) for s in steps]
    }

    return get_localized_values(ret_dict, questionnaire, questionnaire.localized_keys, language)


def serialize_field_option(option, language):
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
        'trigger_field': option.trigger_field if option.trigger_field else '',
        'trigger_step': option.trigger_step if option.trigger_step else ''
    }

    return get_localized_values(ret_dict, option, option.localized_keys, language)


def serialize_field_attr(attr, language):
    """
    Serialize a field attribute, localizing its content depending on the language.

    :param option: the field attribute object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    ret_dict = {
        'id': attr.id,
        'name': attr.name,
        'type': attr.type,
        'value': attr.value
    }

    if attr.type == 'bool':
        ret_dict['value'] = True if ret_dict['value'] == 'True' else False
    elif attr.type == u'localized':
        get_localized_values(ret_dict, ret_dict, ['value'], language)

    return ret_dict


def serialize_field(store, field, language, data=None):
    """
    Serialize a field, localizing its content depending on the language.

    :param field: the field object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    if data is None:
        data = db_prepare_fields_serialization(store, [field])

    if field.template_id is not None:
        f_to_serialize = store.find(models.Field, id=field.template_id).one()
    else:
        f_to_serialize = field

    attrs = {}
    for attr in data['attrs'].get(f_to_serialize.id, {}):
        attrs[attr.name] = serialize_field_attr(attr, language)

    triggered_by_options = []
    _triggered_by_options = store.find(models.FieldOption, models.FieldOption.trigger_field == field.id)
    for trigger in _triggered_by_options:
        triggered_by_options.append({
            'field': trigger.field_id,
            'option': trigger.id
        })

    ret_dict = {
        'id': f_to_serialize.id,
        'instance': field.instance,
        'editable': field.editable,
        'type': f_to_serialize.type,
        'template_id': field.template_id if field.template_id else '',
        'step_id': field.step_id if field.step_id else '',
        'fieldgroup_id': field.fieldgroup_id if field.fieldgroup_id else '',
        'multi_entry': field.multi_entry,
        'required': field.required,
        'preview': field.preview,
        'stats_enabled': field.stats_enabled,
        'attrs': attrs,
        'x': field.x,
        'y': field.y,
        'width': field.width,
        'triggered_by_score': field.triggered_by_score,
        'triggered_by_options':  triggered_by_options,
        'options': [serialize_field_option(o, language) for o in data['options'].get(f_to_serialize.id, [])],
        'children': [serialize_field(store, f, language) for f in data['fields'].get(f_to_serialize.id, [])]
    }

    return get_localized_values(ret_dict, f_to_serialize, field.localized_keys, language)


def serialize_step(store, step, language):
    """
    Serialize a step, localizing its content depending on the language.

    :param step: the step to be serialized.
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    triggered_by_options = []
    _triggered_by_options = store.find(models.FieldOption, models.FieldOption.trigger_step == step.id)
    for trigger in _triggered_by_options:
        triggered_by_options.append({
            'step': trigger.step_id,
            'option': trigger.id
        })

    children = store.find(models.Field, models.Field.step_id == step.id)

    data = db_prepare_fields_serialization(store, children)

    ret_dict = {
        'id': step.id,
        'questionnaire_id': step.questionnaire_id,
        'presentation_order': step.presentation_order,
        'triggered_by_score': step.triggered_by_score,
        'triggered_by_options': triggered_by_options,
        'children': [serialize_field(store, f, language, data) for f in children]
    }

    return get_localized_values(ret_dict, step, step.localized_keys, language)


def serialize_receiver(store, receiver, language, data=None):
    """
    Serialize a receiver description

    :param receiver: the receiver to be serialized
    :param language: the language in which to localize data
    :return: a serializtion of the object
    """
    if data is None:
        data = db_prepare_receivers_serialization(store, [receiver])

    user = data['users'][receiver.id]

    ret_dict = {
        'id': receiver.id,
        'name': user.public_name,
        'username': user.username if GLSettings.memory_copy.simplified_login else '',
        'state': user.state,
        'configuration': receiver.configuration,
        'presentation_order': receiver.presentation_order,
        'can_delete_submission': receiver.can_delete_submission,
        'can_postpone_expiration': receiver.can_postpone_expiration,
        'can_grant_permissions': receiver.can_grant_permissions,
        'contexts': data['contexts'].get(receiver.id, []),
        'picture': data['imgs'].get(user.img_id, '')
    }

    # description and eventually other localized strings should be taken from user model
    get_localized_values(ret_dict, user, ['description'], language)

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


def db_get_public_context_list(store, language):
    subselect = Select(models.ReceiverContext.context_id, distinct=True)

    contexts = store.find(models.Context, models.Context.id.is_in(subselect))

    data = db_prepare_contexts_serialization(store, contexts)

    return [serialize_context(store, context, language, data) for context in contexts]


def db_get_questionnaire_list(store, language):
    questionnaires = store.find(models.Questionnaire)

    return [serialize_questionnaire(store, questionnaire, language) for questionnaire in questionnaires]


def db_get_public_receiver_list(store, language):
    receivers = store.find(models.Receiver,
                           models.Receiver.id == models.User.id,
                           models.User.state != u'disabled')

    data = db_prepare_receivers_serialization(store, receivers)

    return [serialize_receiver(store, receiver, language, data) for receiver in receivers]


@transact
def get_public_resources(store, language):
    return {
        'node': db_serialize_node(store, language),
        'contexts': db_get_public_context_list(store, language),
        'questionnaires': db_get_questionnaire_list(store, language),
        'receivers': db_get_public_receiver_list(store, language),
    }


class PublicResource(BaseHandler):
    check_roles = '*'
    cache_resource = True

    def get(self):
        """
        Get all the public resources.
        """
        return get_public_resources(self.request.language)
