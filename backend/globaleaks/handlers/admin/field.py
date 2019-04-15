# -*- coding: utf-8
#
#   /admin/fields
#   *****
# Implementation of the code executed on handler /admin/fields
#
from sqlalchemy.sql.expression import not_

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import get_trigger_model_by_type, serialize_field
from globaleaks.models import fill_localized_keys
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import Settings
from globaleaks.utils.utility import read_json_file


def db_create_trigger(session, tid, option_id, type, object_id):
    o = get_trigger_model_by_type(type)()
    o.option_id = option_id
    o.object_id = object_id
    session.add(o)


def db_reset_option_triggers(session, type, object_id):
    m = get_trigger_model_by_type(type)
    session.query(m).filter(m.object_id == object_id).delete(synchronize_session='fetch')


def db_update_fieldoption(session, field_id, fieldoption_id, option_dict, language, idx):
    option_dict['field_id'] = field_id

    fill_localized_keys(option_dict, models.FieldOption.localized_keys, language)

    o = None
    if fieldoption_id is not None:
        o = session.query(models.FieldOption).filter(models.FieldOption.id == fieldoption_id).one_or_none()

    if o is None:
        o = models.db_forge_obj(session, models.FieldOption, option_dict)
    else:
        o.update(option_dict)

    o.presentation_order = idx

    return o.id


def db_update_fieldoptions(session, field_id, options, language):
    options_ids = [db_update_fieldoption(session, field_id, option['id'], option, language, idx) for idx, option in enumerate(options)]

    if not options_ids:
        return

    to_remove = session.query(models.FieldOption.id).filter(models.FieldOption.field_id == field_id,
                                                            not_(models.FieldOption.id.in_(options_ids)))

    session.query(models.FieldOption).filter(models.FieldOption.id.in_(to_remove.subquery())).delete(synchronize_session='fetch')


def db_update_fieldattr(session, field_id, attr_name, attr_dict, language):
    attr_dict['name'] = attr_name
    attr_dict['field_id'] = field_id

    if attr_dict['type'] == u'localized' and language is not None:
        fill_localized_keys(attr_dict, ['value'], language)

    o = session.query(models.FieldAttr).filter(models.FieldAttr.field_id == field_id, models.FieldAttr.name == attr_name).one_or_none()
    if o is None:
        o = models.db_forge_obj(session, models.FieldAttr, attr_dict)
    else:
        o.update(attr_dict)

    return o.id


def db_update_fieldattrs(session, field_id, field_attrs, language):
    attrs_ids = [db_update_fieldattr(session, field_id, attr_name, attr, language) for attr_name, attr in field_attrs.items()]

    if not attrs_ids:
        return

    to_remove = session.query(models.FieldAttr.id).filter(models.FieldAttr.field_id == field_id,
                                                                  not_(models.FieldAttr.id.in_(attrs_ids)))

    session.query(models.FieldAttr).filter(models.FieldAttr.id.in_(to_remove.subquery())).delete(synchronize_session='fetch')


def check_field_association(session, tid, field_dict):
    if field_dict.get('fieldgroup_id', '') and session.query(models.Field).filter(models.Field.id == field_dict['fieldgroup_id'],
                                                                                  models.Field.tid != tid).count():
        raise errors.InputValidationError()

    if field_dict.get('template_id', '') and session.query(models.Field).filter(models.Field.id == field_dict['template_id'],
                                                                                not_(models.Field.tid.in_(set([1, tid])))).count():
        raise errors.InputValidationError()

    if field_dict.get('step_id', '') and session.query(models.Field).filter(models.Step.id == field_dict['step_id'],
                                                                            models.Questionnaire.id == models.Step.questionnaire_id,
                                                                            not_(models.Questionnaire.tid.in_(set([1, tid])))).count():
        raise errors.InputValidationError()

    if field_dict.get('fieldgroup_id', ''):
        ancestors = set(fieldtree_ancestors(session, field_dict['fieldgroup_id']))
        if field_dict['id'] == field_dict['fieldgroup_id'] or field_dict['id'] in ancestors:
            raise errors.InputValidationError("Provided field association would cause recursion loop")


def db_create_field(session, tid, field_dict, language):
    """
    Create and add a new field to the session, then return the new serialized object.
    """
    field_dict['tid'] = tid

    fill_localized_keys(field_dict, models.Field.localized_keys, language)

    check_field_association(session, tid, field_dict)

    if field_dict.get('template_id', '') != '':
        if field_dict['template_id'] == 'whistleblower_identity':
            if field_dict.get('step_id', '') == '':
                raise errors.InputValidationError("Cannot associate whistleblower identity field to a fieldgroup")

            q_id = session.query(models.Questionnaire.id) \
                          .filter(models.Questionnaire.id == models.Step.questionnaire_id,
                                  models.Step.id == field_dict['step_id'])

            field = session.query(models.Field) \
                           .filter(models.Field.template_id == u'whistleblower_identity',
                                   models.Field.step_id == models.Step.id,
                                   models.Step.questionnaire_id.in_(q_id.subquery())).one_or_none()

            if field is not None:
                raise errors.InputValidationError("Whistleblower identity field already present")

        field = models.db_forge_obj(session, models.Field, field_dict)

        template = session.query(models.Field).filter(models.Field.id == field_dict['template_id']).one()

        field.label = template.label
        field.hint = template.hint
        field.description = template.description

        attrs = field_dict.get('attrs')
        if not attrs:
            field_attrs = read_json_file(Settings.field_attrs_file)
            attrs = field_attrs.get(field.template_id, {})

        db_update_fieldattrs(session, field.id, attrs, None)

    else:
        field = models.db_forge_obj(session, models.Field, field_dict)
        attrs = field_dict.get('attrs')
        options = field_dict.get('options')

        db_update_fieldattrs(session, field.id, attrs, language)
        db_update_fieldoptions(session, field.id, options, language)

        for trigger in field_dict.get('triggered_by_options', []):
            db_create_trigger(session, tid, trigger['option'], 'field', field.id)

    if field.instance != 'reference':
        for c in field_dict.get('children', []):
            c['tid'] = field.tid
            c['fieldgroup_id'] = field.id
            db_create_field(session, tid, c, language)

    return field


@transact
def create_field(session, tid, field_dict, language):
    """
    Transaction that perform db_create_field
    """
    field = db_create_field(session, tid, field_dict, language)

    return serialize_field(session, tid, field, language)


def db_update_field(session, tid, field_id, field_dict, language):
    field = models.db_get(session, models.Field, models.Field.tid == tid, models.Field.id == field_id)

    check_field_association(session, tid, field_dict)

    fill_localized_keys(field_dict, models.Field.localized_keys, language)

    db_update_fieldattrs(session, field.id, field_dict['attrs'], language)

    db_reset_option_triggers(session, 'field', field.id)

    for trigger in field_dict.get('triggered_by_options', []):
        db_create_trigger(session, tid, trigger['option'], 'field', field.id)

    if field_dict['instance'] != 'reference':
        db_update_fieldoptions(session, field.id, field_dict['options'], language)

        # full update
        field.update(field_dict)

    else:
        # partial update
        field.update({
          'label': field_dict['label'],
          'hint': field_dict['hint'],
          'description': field_dict['description'],
          'template_override_id': field_dict['template_override_id'],
          'x': field_dict['x'],
          'y': field_dict['y'],
          'width': field_dict['width'],
          'required': field_dict['required']
        })

    return field


@transact
def update_field(session, tid, field_id, field, language):
    """
    Update the specified field with the details.
    """
    field = db_update_field(session, tid, field_id, field, language)

    return serialize_field(session, tid, field, language)


@transact
def delete_field(session, tid, field_id):
    """
    Delete the field object corresponding to field_id
    """
    field = models.db_get(session, models.Field, models.Field.tid == tid, models.Field.id == field_id)

    if not field.editable:
        raise errors.ForbiddenOperation

    if field.instance == 'template' and session.query(models.Field).filter(models.Field.tid == tid, models.Field.template_id == field.id).count():
        raise errors.InputValidationError("Cannot remove the field template as it is used by one or more questionnaires")

    session.delete(field)


def fieldtree_ancestors(session, id):
    """
    Given a field_id, recursively extract its parents.
    """
    field = session.query(models.Field).filter(models.Field.id == id).one_or_none()
    if field.fieldgroup_id is not None:
        yield field.fieldgroup_id
        yield fieldtree_ancestors(session, field.fieldgroup_id)


@transact
def get_fieldtemplate_list(session, tid, language):
    """
    Serialize all the field templates localizing their content depending on the language.
    """
    templates = session.query(models.Field).filter(models.Field.tid.in_(set([1, tid])),
                                                   models.Field.instance == u'template',
                                                   models.Field.fieldgroup_id == None)

    return [serialize_field(session, tid, f, language) for f in templates]


class FieldTemplatesCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return a list of all the fields templates.
        """
        return get_fieldtemplate_list(self.request.tid, self.request.language)

    def post(self):
        """
        Create a field template.
        """
        validator = requests.AdminFieldDesc if self.request.language is not None else requests.AdminFieldDescRaw

        request = self.validate_message(self.request.content.read(), validator)

        return create_field(self.request.tid, request, self.request.language)


class FieldTemplateInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, field_id):
        """
        Update a field template
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminFieldDesc)

        return update_field(self.request.tid,
                            field_id,
                            request,
                            self.request.language)

    def delete(self, field_id):
        """
        Delete a field template.
        """
        return delete_field(self.request.tid, field_id)


class FieldsCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def post(self):
        """
        Create a field.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminFieldDesc)

        return create_field(self.request.tid,
                            request,
                            self.request.language)


class FieldInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, field_id):
        """
        Update a field.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminFieldDesc)

        return update_field(self.request.tid,
                            field_id,
                            request,
                            self.request.language)

    def delete(self, field_id):
        """
        Delete a field.
        """
        return delete_field(self.request.tid, field_id)
