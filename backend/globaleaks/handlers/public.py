# -*- coding: utf-8 -*-
#
# Handlers dealing with public API exporting main platform configuration/resources
import copy

from globaleaks import models, LANGUAGES_SUPPORTED, LANGUAGES_SUPPORTED_CODES
from globaleaks.handlers.admin.file import db_get_file
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import ConfigFactory
from globaleaks.models.l10n import NodeL10NFactory
from globaleaks.orm import transact
from globaleaks.state import State
from globaleaks.utils.sets import merge_dicts
from globaleaks.utils.structures import get_localized_values

special_fields = ['whistleblower_identity']


def db_prepare_contexts_serialization(session, contexts):
    data = {'imgs': {}, 'receivers': {}}

    contexts_ids = [c.id for c in contexts]

    if contexts_ids:
        for o in session.query(models.ContextImg).filter(models.ContextImg.id.in_(contexts_ids)):
            data['imgs'][o.id] = o.data

        for o in session.query(models.ReceiverContext).filter(models.ReceiverContext.context_id.in_(contexts_ids)).order_by(models.ReceiverContext.presentation_order):
            if o.context_id not in data['receivers']:
                data['receivers'][o.context_id] = []

            data['receivers'][o.context_id].append(o.receiver_id)

    return data


def db_prepare_receivers_serialization(session, receivers):
    data = {'users': {}, 'imgs': {}}

    receivers_ids = [r.id for r in receivers]

    if receivers_ids:
        for o in session.query(models.User).filter(models.User.id.in_(receivers_ids)):
            data['users'][o.id] = o

        for o in session.query(models.UserImg).filter(models.UserImg.id.in_(receivers_ids)):
            data['imgs'][o.id] = o.data

    return data


def db_prepare_fields_serialization(session, fields):
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
        fs = session.query(models.Field).filter(models.Field.fieldgroup_id.in_(tmp))

        tmp = []
        for f in fs:
            tmp.append(f.id)
            if f.template_id is not None:
                tmp.append(f.template_id)

            if f.fieldgroup_id not in ret['fields']:
                ret['fields'][f.fieldgroup_id] = []
            ret['fields'][f.fieldgroup_id].append(f)

        fields_ids.extend(tmp)

    if fields_ids:
        objs = session.query(models.FieldAttr).filter(models.FieldAttr.field_id.in_(fields_ids))
        for obj in objs:
            if obj.field_id not in ret['attrs']:
                ret['attrs'][obj.field_id] = []
            ret['attrs'][obj.field_id].append(obj)

        objs = session.query(models.FieldOption)\
                    .filter(models.FieldOption.field_id.in_(fields_ids)) \
                    .order_by(models.FieldOption.presentation_order)
        for obj in objs:
            if obj.field_id not in ret['options']:
                ret['options'][obj.field_id] = []
            ret['options'][obj.field_id].append(obj)

        objs = session.query(models.FieldOption).filter(models.FieldOption.trigger_field.in_(fields_ids))
        for obj in objs:
            if obj.field_id not in ret['triggers']:
                ret['triggers'][obj.field_id] = []
            ret['triggers'][obj.field_id].append(obj)

    return ret


def db_serialize_node(session, tid, language):
    """
    Serialize node info.
    """
    # Contexts and Receivers relationship
    configured = session.query(models.ReceiverContext).filter(models.ReceiverContext.context_id == models.Context.id,
                                                              models.Context.tid == tid).count() > 0

    node = ConfigFactory(session, tid, 'public_node').serialize()

    misc_dict = {
        'languages_enabled': models.EnabledLanguage.list(session, tid) if node['wizard_done'] else list(LANGUAGES_SUPPORTED_CODES),
        'languages_supported': LANGUAGES_SUPPORTED,
        'configured': configured,
        'accept_submissions': State.accept_submissions,
        'logo': db_get_file(session, tid, u'logo'),
        'favicon': db_get_file(session, tid, u'favicon'),
        'css': db_get_file(session, tid, u'css'),
        'homepage': db_get_file(session, tid, u'homepage'),
        'script': db_get_file(session, tid, u'script')
    }

    l10n_dict = NodeL10NFactory(session, tid).localized_dict(language)

    return merge_dicts(node, l10n_dict, misc_dict)


def serialize_context(session, context, language, data=None):
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


def serialize_questionnaire(session, tid, questionnaire, language):
    """
    Serialize the specified questionnaire

    :param session: the session on which perform queries.
    :param language: the language in which to localize data.
    :return: a dictionary representing the serialization of the questionnaire.
    """
    steps = session.query(models.Step).filter(models.Step.questionnaire_id == questionnaire.id,
                                              models.Questionnaire.id == questionnaire.id)

    ret_dict = {
        'id': questionnaire.id,
        'editable': questionnaire.editable and questionnaire.tid == tid,
        'name': questionnaire.name,
        'steps': sorted([serialize_step(session, tid, s, language) for s in steps],
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


def serialize_field(session, tid, field, language, data=None):
    """
    Serialize a field, localizing its content depending on the language.

    :param field: the field object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    if data is None:
        data = db_prepare_fields_serialization(session, [field])

    if field.template_id is not None:
        f_to_serialize = session.query(models.Field).filter(models.Field.id == field.template_id, models.Field.tid == field.tid).one_or_none()
    else:
        f_to_serialize = field

    attrs = {}
    for attr in data['attrs'].get(field.id, {}):
        attrs[attr.name] = serialize_field_attr(attr, language)

    triggered_by_options = []
    _triggered_by_options = session.query(models.FieldOption).filter(models.FieldOption.trigger_field == field.id, models.Field.tid == field.tid)
    for trigger in _triggered_by_options:
        triggered_by_options.append({
            'field': trigger.field_id,
            'option': trigger.id
        })

    ret_dict = {
        'id': field.id,
        'instance': field.instance,
        'editable': field.editable and field.tid == tid,
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
        'children': [serialize_field(session, tid, f, language) for f in data['fields'].get(f_to_serialize.id, [])]
    }

    return get_localized_values(ret_dict, f_to_serialize, field.localized_keys, language)


def serialize_step(session, tid, step, language):
    """
    Serialize a step, localizing its content depending on the language.

    :param step: the step to be serialized.
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    children = session.query(models.Field).filter(models.Field.step_id == step.id)

    data = db_prepare_fields_serialization(session, children)

    ret_dict = {
        'id': step.id,
        'questionnaire_id': step.questionnaire_id,
        'presentation_order': step.presentation_order,
        'children': [serialize_field(session, tid, f, language, data) for f in children]
    }

    return get_localized_values(ret_dict, step, step.localized_keys, language)


def serialize_receiver(session, receiver, language, data=None):
    """
    Serialize a receiver description

    :param receiver: the receiver to be serialized
    :param language: the language in which to localize data
    :return: a serializtion of the object
    """
    if data is None:
        data = db_prepare_receivers_serialization(session, [receiver])

    user = data['users'][receiver.id]

    ret_dict = {
        'id': receiver.id,
        'username': user.username,
        'name': user.name,
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


def db_get_public_context_list(session, tid, language):
    contexts = session.query(models.Context).filter(models.Context.id == models.ReceiverContext.context_id,
                                                    models.Context.tid == tid)

    data = db_prepare_contexts_serialization(session, contexts)

    return [serialize_context(session, context, language, data) for context in contexts]


def db_get_questionnaire_list(session, tid, language):
    questionnaires = session.query(models.Questionnaire).filter(models.Questionnaire.tid.in_(set([1, tid])),
                                                                models.Context.questionnaire_id == models.Questionnaire.id,
                                                                models.Context.id == models.ReceiverContext.context_id,
                                                                models.Context.tid == tid)

    return [serialize_questionnaire(session, tid, questionnaire, language) for questionnaire in questionnaires]


def db_get_public_receiver_list(session, tid, language):
    receivers = session.query(models.Receiver).filter(models.Receiver.id == models.User.id,
                                                      models.User.state != u'disabled',
                                                      models.User.tid == tid)

    data = db_prepare_receivers_serialization(session, receivers)

    ret = []
    for receiver in receivers:
        x = serialize_receiver(session, receiver, language, data)
        if not State.tenant_cache[tid].simplified_login:
            x['username'] = ''
        ret.append(x)

    return ret


@transact
def get_public_resources(session, tid, language):
    return {
        'node': db_serialize_node(session, tid, language),
        'contexts': db_get_public_context_list(session, tid, language),
        'questionnaires': db_get_questionnaire_list(session, tid, language),
        'receivers': db_get_public_receiver_list(session, tid, language),
    }


class PublicResource(BaseHandler):
    check_roles = '*'
    cache_resource = True

    def get(self):
        """
        Get all the public resources.
        """
        return get_public_resources(self.request.tid, self.request.language)
