# -*- coding: utf-8 -*-
#
# Handlers dealing with public API exporting main platform configuration/resources
import copy

from sqlalchemy import or_

from globaleaks import models, LANGUAGES_SUPPORTED, LANGUAGES_SUPPORTED_CODES
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin.submission_statuses import db_get_submission_statuses
from globaleaks.models import get_localized_values
from globaleaks.models.config import ConfigFactory, ConfigL10NFactory
from globaleaks.models.enums import EnumContextStatus
from globaleaks.orm import transact
from globaleaks.state import State
from globaleaks.utils.sets import merge_dicts


special_fields = ['whistleblower_identity']


trigger_map = {
    'field': models.FieldOptionTriggerField,
    'step': models.FieldOptionTriggerStep
}


def db_get_triggers_by_type(session, type, object_id):
    """
    Transaction for retrieving field triggers associated to an object given the type of trigger

    :param session: An ORM session
    :param type: The type of trigger involved in the lookup
    :param object_id: The object on which performing the lookup
    :return: A list of triggers descriptors
    """
    ret = []

    m = trigger_map[type]
    for x in session.query(models.FieldOption.field_id, models.FieldOption.id, m.sufficient) \
                    .filter(models.FieldOption.id == m.option_id, m.object_id == object_id):
        ret.append({'field': x[0], 'option': x[1], 'sufficient': x[2]})

    return ret


def db_prepare_contexts_serialization(session, contexts):
    """
    Transaction to prepare and optimize context serialization

    :param session: An ORM session
    :param contexts: The list of context for which preparing the serialization
    :return: The set of retrieved objects necessary for optimizing the serialization
    """
    data = {'imgs': {}, 'receivers': {}}

    contexts_ids = [c.id for c in contexts]

    if contexts_ids:
        for o in session.query(models.ContextImg).filter(models.ContextImg.id.in_(contexts_ids)):
            data['imgs'][o.id] = o.data

        for o in session.query(models.ReceiverContext).filter(models.ReceiverContext.context_id.in_(contexts_ids)).order_by(models.ReceiverContext.order):
            if o.context_id not in data['receivers']:
                data['receivers'][o.context_id] = []

            data['receivers'][o.context_id].append(o.receiver_id)

    return data


def db_prepare_receivers_serialization(session, receivers):
    """
    Transaction to prepare and optimize receiver serialization

    :param session: An ORM session
    :param receivers: The list of receivers for which preparing the serialization
    :return: The set of retrieved objects necessary for optimizing the serialization
    """
    data = {'imgs': {}}

    receivers_ids = [r.id for r in receivers]

    if receivers_ids:
        for o in session.query(models.UserImg).filter(models.UserImg.id.in_(receivers_ids)):
            data['imgs'][o.id] = o.data

    return data


def db_prepare_fields_serialization(session, fields):
    """
    Transaction to prepare and optimize fields serialization

    :param session: An ORM session
    :param fields: The list of receivers for which preparing the serialization
    :return: The set of retrieved objects necessary for optimizing the serialization
    """
    ret = {
        'fields': {},
        'attrs': {},
        'options': {}
    }

    fields_ids = []
    for f in fields:
        fields_ids.append(f.id)
        if f.template_id is not None:
            fields_ids.append(f.template_id)
        if f.template_override_id is not None:
            fields_ids.append(f.template_override_id)

    tmp = copy.deepcopy(fields_ids)
    while tmp:
        fs = session.query(models.Field).filter(models.Field.fieldgroup_id.in_(tmp))

        tmp = []
        for f in fs:
            tmp.append(f.id)
            if f.template_id is not None:
                tmp.append(f.template_id)
            if f.template_override_id is not None:
                tmp.append(f.template_override_id)

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
                    .order_by(models.FieldOption.order)
        for obj in objs:
            if obj.field_id not in ret['options']:
                ret['options'][obj.field_id] = []
            ret['options'][obj.field_id].append(obj)

    return ret


def db_serialize_node(session, tid, language):
    """
    Serialize the public node configuration.

    :param session: An ORM session
    :param tid: A tenant ID
    :param language: The language to be used during serialization
    :return: The serialization of the public node configuration
    """
    node_dict = ConfigFactory(session, tid).serialize('public_node')
    l10n_dict = ConfigL10NFactory(session, tid,).serialize('node', language)

    ret_dict = merge_dicts(node_dict, l10n_dict)

    ret_dict['root_tenant'] = tid == 1
    ret_dict['languages_enabled'] = models.EnabledLanguage.list(session, tid) if node_dict['wizard_done'] else list(LANGUAGES_SUPPORTED_CODES)
    ret_dict['languages_supported'] = LANGUAGES_SUPPORTED

    records = session.query(models.File.id, models.File.data).filter(models.File.tid == tid, models.File.id.in_(['css', 'logo', 'script']))
    for x in records:
        ret_dict[x[0]] = True

    if tid != 1:
        root_tenant_node = ConfigFactory(session, 1)

        for varname in ['version', 'version_db', 'latest_version']:
            ret_dict[varname] = root_tenant_node.get_val(varname)

        if language not in models.EnabledLanguage.list(session, tid):
            language = root_tenant_node.get_val('default_language')

        root_tenant_l10n = ConfigL10NFactory(session, 1)

        if ret_dict['mode'] != 'default':
            ret_dict['footer'] = root_tenant_l10n.get_val('footer', language)
            ret_dict['whistleblowing_question'] = root_tenant_l10n.get_val('whistleblowing_question', language)
            ret_dict['whistleblowing_button'] = root_tenant_l10n.get_val('whistleblowing_button', language)
            ret_dict['enable_disclaimer'] = root_tenant_node.get_val('enable_disclaimer')
            ret_dict['disclaimer_title'] = root_tenant_l10n.get_val('disclaimer_title', language)
            ret_dict['disclaimer_text'] = root_tenant_l10n.get_val('disclaimer_text', language)

            records = session.query(models.File.id, models.File.data).filter(models.File.tid == 1, models.File.id.in_(['css', 'logo', 'script']))
            for x in records:
                if not ret_dict.get(x[0]):
                    ret_dict[x[0]] = True

    return ret_dict


def serialize_context(session, context, language, data=None):
    """
    Serialize a context.

    :param session: An ORM session
    :param context: The context to be serialized
    :param language: The language to be used during serialization
    :param data: The dictionary of prefetched resources
    """
    ret_dict = {
        'id': context.id,
        'status': context.status,
        'order': context.order,
        'languages': context.languages,
        'tip_timetolive': context.tip_timetolive,
        'select_all_receivers': context.select_all_receivers,
        'maximum_selectable_receivers': context.maximum_selectable_receivers,
        'show_recipients_details': context.show_recipients_details,
        'allow_recipients_selection': context.allow_recipients_selection,
        'show_small_receiver_cards': context.show_small_receiver_cards,
        'enable_comments': context.enable_comments,
        'enable_messages': context.enable_messages,
        'enable_two_way_comments': context.enable_two_way_comments,
        'enable_two_way_messages': context.enable_two_way_messages,
        'enable_attachments': context.enable_attachments,
        'enable_rc_to_wb_files': context.enable_rc_to_wb_files,
        'score_threshold_medium': context.score_threshold_medium,
        'score_threshold_high': context.score_threshold_high,
        'score_receipt_text_custom': context.score_receipt_text_custom,
        'score_receipt_text_l': context.score_receipt_text_l,
        'score_receipt_text_m': context.score_receipt_text_m,
        'score_receipt_text_h': context.score_receipt_text_h,
        'score_threshold_receipt': context.score_threshold_receipt,
        'show_receivers_in_alphabetical_order': context.show_receivers_in_alphabetical_order,
        'show_steps_navigation_interface': context.show_steps_navigation_interface,
        'questionnaire_id': context.questionnaire_id,
        'additional_questionnaire_id': context.additional_questionnaire_id,
        'receivers': data['receivers'].get(context.id, []),
        'picture': data['imgs'].get(context.id, '')
    }

    return get_localized_values(ret_dict, context, context.localized_keys, language)


def serialize_field_option(option, language):
    """
    Serialize a field option.

    :param option: The option to be serialized
    :param language: The language to be used during serialization
    :return: The serialized resource
    """
    ret_dict = {
        'id': option.id,
        'order': option.order,
        'block_submission': option.block_submission,
        'score_points': option.score_points,
        'score_type': option.score_type,
        'trigger_receiver': option.trigger_receiver
    }

    return get_localized_values(ret_dict, option, option.localized_keys, language)


def serialize_field_attr(attr, language):
    """
    Serialize a field attribute.

    :param attr: The option to be serialized
    :param language: The language to be used during serialization
    :return: The serialized resource
    """
    ret_dict = {
        'id': attr.id,
        'name': attr.name,
        'type': attr.type,
        'value': attr.value
    }

    if attr.type == 'localized':
        get_localized_values(ret_dict, ret_dict, ['value'], language)

    return ret_dict


def serialize_field(session, tid, field, language, data=None, serialize_templates=True):
    """
    Serialize a field

    :param session: An ORM session
    :param tid: A tenant ID
    :param field: The option to be serialized
    :param language: The language to be used during serialization
    :param data: The dictionary of prefetched resources
    :param serialize_templates: A boolean to require template serialization
    :return: The serialized resource
    """
    if data is None:
        data = db_prepare_fields_serialization(session, [field])

    f_to_serialize = field
    if field.template_override_id is not None and serialize_templates is True:
        f_to_serialize = session.query(models.Field).filter(models.Field.id == field.template_override_id).one_or_none()
    elif field.template_id is not None and serialize_templates is True:
        f_to_serialize = session.query(models.Field).filter(models.Field.id == field.template_id).one_or_none()

    attrs = {}
    if field.template_id is None or field.template_id in special_fields:
        for attr in data['attrs'].get(field.id, {}):
            attrs[attr.name] = serialize_field_attr(attr, language)
    else:
        for attr in data['attrs'].get(field.template_id, {}):
            attrs[attr.name] = serialize_field_attr(attr, language)

    children = [serialize_field(session, tid, f, language) for f in data['fields'].get(f_to_serialize.id, [])]
    children.sort(key=lambda f: (f['y'], f['x']))

    ret_dict = {
        'id': field.id,
        'instance': field.instance,
        'editable': field.editable and field.tid == tid,
        'type': f_to_serialize.type,
        'template_id': field.template_id if field.template_id else '',
        'template_override_id': field.template_override_id if field.template_override_id else '',
        'step_id': field.step_id if field.step_id else '',
        'fieldgroup_id': field.fieldgroup_id if field.fieldgroup_id else '',
        'multi_entry': f_to_serialize.multi_entry,
        'required': field.required,
        'preview': field.preview,
        'encrypt': field.encrypt,
        'attrs': attrs,
        'x': field.x,
        'y': field.y,
        'width': field.width,
        'triggered_by_score': field.triggered_by_score,
        'triggered_by_options': db_get_triggers_by_type(session, 'field', field.id),
        'options': [serialize_field_option(o, language) for o in data['options'].get(f_to_serialize.id, [])],
        'children': children
    }

    return get_localized_values(ret_dict, field, field.localized_keys, language)


def serialize_step(session, tid, step, language, serialize_templates=True):
    """
    Serialize a step.

    :param session: An ORM session
    :param tid: A tenant ID
    :param step: The option to be serialized
    :param language: The language to be used during serialization
    :param serialize_templates: A boolean to require template serialization
    :return: The serialized resource
    """
    children = session.query(models.Field).filter(models.Field.step_id == step.id)

    data = db_prepare_fields_serialization(session, children)

    children = [serialize_field(session, tid, f, language, data, serialize_templates=serialize_templates) for f in children]
    children.sort(key=lambda f: (f['y'], f['x']))

    ret_dict = {
        'id': step.id,
        'questionnaire_id': step.questionnaire_id,
        'order': step.order,
        'triggered_by_score': step.triggered_by_score,
        'triggered_by_options': db_get_triggers_by_type(session, 'step', step.id),
        'children': children
    }

    return get_localized_values(ret_dict, step, step.localized_keys, language)


def serialize_questionnaire(session, tid, questionnaire, language, serialize_templates=True):
    """
    Serialize a questionnaire.

    :param session: An ORM session
    :param tid: A tenant ID
    :param questionnaire: A questionnaire model
    :param language: The language to be used during serialization
    :param serialize_templates: A boolean to require template serialization
    :return: The serialized resource
    """
    steps = session.query(models.Step).filter(models.Step.questionnaire_id == questionnaire.id,
                                              models.Questionnaire.id == questionnaire.id) \
                                       .order_by(models.Step.order)

    ret_dict = {
        'id': questionnaire.id,
        'editable': questionnaire.editable and questionnaire.tid == tid,
        'name': questionnaire.name,
        'steps': [serialize_step(session, tid, s, language, serialize_templates=serialize_templates) for s in steps]
    }

    return get_localized_values(ret_dict, questionnaire, questionnaire.localized_keys, language)


def serialize_receiver(session, user, language, data=None):
    """
    Serialize a receiver.

    :param session: An ORM session
    :param user: The model to be serialized
    :param language: The language to be used during serialization
    :param data: The dictionary of prefetched resources
    :return: The serialized resource
    """
    if data is None:
        data = db_prepare_receivers_serialization(session, [user])

    ret_dict = {
        'id': user.id,
        'username': user.username,
        'name': user.public_name,
        'state': user.state,
        'encryption': user.crypto_pub_key != '',
        'recipient_configuration': user.recipient_configuration,
        'can_delete_submission': user.can_delete_submission,
        'can_postpone_expiration': user.can_postpone_expiration,
        'can_grant_permissions': user.can_grant_permissions,
        'picture': data['imgs'].get(user.id, '')
    }

    return get_localized_values(ret_dict, user, user.localized_keys, language)


def db_get_questionnaires(session, tid, language):
    """
    Transaction that serialize the list of public questionnaires

    :param session: An ORM session
    :param tid: The tenant ID
    :param language: The language to be used for the serialization
    :return: A list of contexts descriptors
    """
    questionnaires = session.query(models.Questionnaire) \
                            .filter(models.Questionnaire.tid.in_(set([1, tid])),
                                    or_(models.Context.questionnaire_id == models.Questionnaire.id,
                                        models.Context.additional_questionnaire_id == models.Questionnaire.id),
                                    models.Context.status != EnumContextStatus.disabled.value,
                                    models.Context.tid == tid)

    return [serialize_questionnaire(session, tid, questionnaire, language) for questionnaire in questionnaires]


def db_get_contexts(session, tid, language):
    """
    Transaction that serialize the list of public contexts

    :param session: An ORM session
    :param tid: The tenant ID
    :param language: The language to be used for the serialization
    :return: A list of contexts descriptors
    """
    ret = []

    contexts = session.query(models.Context).filter(models.Context.status != EnumContextStatus.disabled.value,
                                                    models.Context.tid == tid)

    data = db_prepare_contexts_serialization(session, contexts)

    for context in contexts:
        if not context.languages or language.lower() in [x.strip().lower() for x in context.languages.split(',')]:
            ret.append(serialize_context(session, context, language, data))

    return ret


def db_get_receivers(session, tid, language):
    """
    Transaction that serialize the list of public receivers

    :param session: An ORM session
    :param tid: The tenant ID
    :param language: The language to be used for the serialization
    :return: A list of receivers descriptors
    """
    receivers = session.query(models.User).filter(models.User.role == models.EnumUserRole.receiver.value,
                                                  models.User.state != 'disabled',
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
    """
    Transaction that compose the public API

    :param session: An ORM session
    :param tid: The tenant ID
    :param language: The language to be used for serialization
    :return: The public API descriptor
    """
    ret = {
        'node': db_serialize_node(session, tid, language),
        'contexts': db_get_contexts(session, tid, language),
        'questionnaires': db_get_questionnaires(session, tid, language),
        'receivers': db_get_receivers(session, tid, language),
        'submission_statuses': db_get_submission_statuses(session, tid, language)
    }

    if ret['node']['do_not_expose_users_names']:
        for receiver in ret['receivers']:
            receiver['name'] = ret['node']['name']

    return ret


class PublicResource(BaseHandler):
    """
    Handler responsible of serving the public API
    """
    check_roles = 'none'
    cache_resource = True

    def get(self):
        """
        Get the public resource
        """
        return get_public_resources(self.request.tid, self.request.language)
