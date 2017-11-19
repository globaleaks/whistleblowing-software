# -*- coding: utf-8
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
from globaleaks.state import State
from globaleaks.utils.sets import merge_dicts
from globaleaks.utils.structures import get_localized_values


def db_prepare_contexts_serialization(store, tid, contexts):
    data = {'imgs': {}, 'receivers': {}}

    contexts_ids = [c.id for c in contexts]

    for o in store.find(models.Context, In(models.ContextImg.id, contexts_ids), tid=tid):
        data['imgs'][o.id] = o.data

    for o in store.find(models.ReceiverContext, In(models.ReceiverContext.context_id, contexts_ids), tid=tid).order_by(models.ReceiverContext.presentation_order):
        if o.context_id not in data['receivers']:
            data['receivers'][o.context_id] = []
        data['receivers'][o.context_id].append(o.receiver_id)

    return data


def db_prepare_receivers_serialization(store, tid, receivers):
    data = {'users': {}, 'imgs': {}}

    receivers_ids = [r.id for r in receivers]

    for o in store.find(models.User, In(models.User.id, receivers_ids), tid=tid):
        data['users'][o.id] = o

    for o in store.find(models.UserImg, In(models.UserImg.id, receivers_ids), tid=tid):
        data['imgs'][o.id] = o.data

    return data


def db_prepare_fields_serialization(store, tid, fields):
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
        fs = store.find(models.Field, In(models.Field.fieldgroup_id, tmp), tid=tid)

        tmp = []
        for f in fs:
            tmp.append(f.id)
            if f.template_id is not None:
                tmp.append(f.template_id)

            if f.fieldgroup_id not in ret['fields']:
                ret['fields'][f.fieldgroup_id] = []
            ret['fields'][f.fieldgroup_id].append(f)

        fields_ids.extend(tmp)

    objs = store.find(models.FieldAttr, In(models.FieldAttr.field_id, fields_ids), tid=tid)
    for obj in objs:
        if obj.field_id not in ret['attrs']:
            ret['attrs'][obj.field_id] = []
        ret['attrs'][obj.field_id].append(obj)

    objs = store.find(models.FieldOption, In(models.FieldOption.field_id, fields_ids), tid=tid)\
                .order_by(models.FieldOption.presentation_order)
    for obj in objs:
        if obj.field_id not in ret['options']:
            ret['options'][obj.field_id] = []
        ret['options'][obj.field_id].append(obj)

    objs = store.find(models.FieldOption, In(models.FieldOption.trigger_field, fields_ids), tid=tid)
    for obj in objs:
        if obj.field_id not in ret['triggers']:
            ret['triggers'][obj.field_id] = []
        ret['triggers'][obj.field_id].append(obj)

    return ret


def db_serialize_node(store, tid, language):
    """
    Serialize node info.
    """
    # Contexts and Receivers relationship
    configured = store.find(models.ReceiverContext, tid=tid).count() > 0

    ro_node = NodeFactory(store, tid).public_export()

    misc_dict = {
        'languages_enabled': l10n.EnabledLanguage.list(store, tid),
        'languages_supported': LANGUAGES_SUPPORTED,
        'configured': configured,
        'accept_submissions': State.accept_submissions,
        'logo': db_get_file(store, tid, u'logo'),
        'favicon': db_get_file(store, tid, u'favicon'),
        'css': db_get_file(store, tid, u'css'),
        'homepage': db_get_file(store, tid, u'homepage'),
        'script': db_get_file(store, tid, u'script')
    }

    l10n_dict = NodeL10NFactory(store, tid).localized_dict(language)

    return merge_dicts(ro_node, l10n_dict, misc_dict)


@transact
def serialize_node(store, tid, language):
    return db_serialize_node(store, tid, language)


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
        'picture': data['imgs'].get(context.id, '')
    }

    return get_localized_values(ret_dict, context, context.localized_keys, language)


def serialize_questionnaire(store, questionnaire, language):
    """
    Serialize the specified questionnaire

    :param store: the store on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the questionnaire.
    """
    steps = store.find(models.Step, questionnaire_id=questionnaire.id, tid=questionnaire.tid)

    ret_dict = {
        'id': questionnaire.id,
        'editable': questionnaire.editable,
        'name': questionnaire.name,
        'steps': sorted([serialize_step(store, s, language) for s in steps],
                        key=lambda x: x['presentation_order'])
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
        'trigger_field': option.trigger_field if option.trigger_field else ''
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
        data = db_prepare_fields_serialization(store, field.tid, [field])

    if field.template_id is not None:
        f_to_serialize = store.find(models.Field, id=field.template_id, tid=field.tid).one()
    else:
        f_to_serialize = field

    attrs = {}
    for attr in data['attrs'].get(f_to_serialize.id, {}):
        attrs[attr.name] = serialize_field_attr(attr, language)

    triggered_by_options = []
    _triggered_by_options = store.find(models.FieldOption, models.FieldOption.trigger_field == field.id, tid=field.tid)
    for trigger in _triggered_by_options:
        triggered_by_options.append({
            'field': trigger.field_id,
            'option': trigger.id
        })

    ret_dict = {
        'id': field.id,
        'instance': field.instance,
        'editable': field.editable,
        'type': f_to_serialize.type,
        'template_id': field.template_id if field.template_id else '',
        'step_id': field.step_id if field.step_id else '',
        'fieldgroup_id': field.fieldgroup_id if field.fieldgroup_id else '',
        'multi_entry': field.multi_entry,
        'required': f_to_serialize.required,
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
    children = store.find(models.Field, models.Field.step_id == step.id, tid=step.tid)

    data = db_prepare_fields_serialization(store, step.tid, children)

    ret_dict = {
        'id': step.id,
        'questionnaire_id': step.questionnaire_id,
        'presentation_order': step.presentation_order,
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
        data = db_prepare_receivers_serialization(store, receiver.tid, [receiver])

    user = data['users'][receiver.id]

    ret_dict = {
        'id': receiver.id,
        'name': user.public_name,
        'username': user.username if State.tenant_cache[receiver.tid].simplified_login else '',
        'state': user.state,
        'configuration': receiver.configuration,
        'can_delete_submission': receiver.can_delete_submission,
        'can_postpone_expiration': receiver.can_postpone_expiration,
        'can_grant_permissions': receiver.can_grant_permissions,
        'picture': data['imgs'].get(user.id, '')
    }

    # description and eventually other localized strings should be taken from user model
    get_localized_values(ret_dict, user, ['description'], language)

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


def db_get_public_context_list(store, tid, language):
    subselect = Select(models.ReceiverContext.context_id,
                       models.ReceiverContext.tid==tid,
                       distinct=True)

    contexts = store.find(models.Context, models.Context.id.is_in(subselect))

    data = db_prepare_contexts_serialization(store, tid, contexts)

    return [serialize_context(store, context, language, data) for context in contexts]


def db_get_questionnaire_list(store, tid, language):
    questionnaires = store.find(models.Questionnaire, tid=tid)

    return [serialize_questionnaire(store, questionnaire, language) for questionnaire in questionnaires]


def db_get_public_receiver_list(store, tid, language):
    receivers = store.find(models.Receiver,
                           models.Receiver.id == models.User.id,
                           models.User.state != u'disabled',
                           models.User.tid == tid)

    data = db_prepare_receivers_serialization(store, tid, receivers)

    return [serialize_receiver(store, receiver, language, data) for receiver in receivers]


@transact
def get_public_resources(store, tid, language):
    return {
        'node': db_serialize_node(store, tid, language),
        'contexts': db_get_public_context_list(store, tid, language),
        'questionnaires': db_get_questionnaire_list(store, tid, language),
        'receivers': db_get_public_receiver_list(store, tid, language),
    }


class PublicResource(BaseHandler):
    check_roles = '*'
    cache_resource = True

    def get(self):
        """
        Get all the public resources.
        """
        return get_public_resources(self.request.tid, self.request.language)
