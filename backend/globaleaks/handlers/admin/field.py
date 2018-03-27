# -*- coding: utf-8
#
#   /admin/fields
#   *****
# Implementation of the code executed on handler /admin/fields
#
from sqlalchemy.sql.expression import not_

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import serialize_field
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import Settings
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import read_json_file


def db_add_field_attrs(session, field_id, field_attrs):
    for attr_name, attr_dict in field_attrs.items():
        x = session.query(models.FieldAttr) \
                   .filter(models.FieldAttr.field_id == field_id,
                           models.FieldAttr.name == attr_name).one_or_none()
        if x is None:
            attr_dict['name'] = attr_name
            attr_dict['field_id'] = field_id
            models.db_forge_obj(session, models.FieldAttr, attr_dict)


def db_update_fieldoption(session, tid, field_id, fieldoption_id, option_dict, language, idx):
    option_dict['tid'] = tid
    option_dict['field_id'] = field_id

    fill_localized_keys(option_dict, models.FieldOption.localized_keys, language)

    o = None
    if fieldoption_id is not None:
        o = session.query(models.FieldOption).filter(models.FieldOption.id == fieldoption_id,
                                                     models.FieldOption.field_id == models.Field.id,
                                                     models.Field.tid == tid).one_or_none()

    if o is None:
        o = models.db_forge_obj(session, models.FieldOption, option_dict)
    else:
        o.update(option_dict)

    o.presentation_order = idx

    return o.id


def db_update_fieldoptions(session, tid, field_id, options, language):
    """
    Update options

    :param session: the session on which perform queries.
    :param field_id: the field_id on wich bind the provided options
    :param language: the language of the option definition dict
    """
    options_ids = [db_update_fieldoption(session, tid, field_id, option['id'], option, language, idx) for idx, option in enumerate(options)]

    if options_ids:
        ids_to_remove = session.query(models.FieldOption.id).filter(models.FieldOption.field_id == field_id,
                                                                    not_(models.FieldOption.id.in_(options_ids)),
                                                                    models.FieldOption.field_id == models.Field.id,
                                                                    models.Field.tid == tid)

        session.query(models.FieldOption).filter(models.FieldOption.id.in_(ids_to_remove.subquery())).delete(synchronize_session='fetch')


def db_update_fieldattr(session, tid, field_id, attr_name, attr_dict, language):
    attr_dict['name'] = attr_name
    attr_dict['field_id'] = field_id
    attr_dict['tid'] = tid

    if attr_dict['type'] == 'bool':
        attr_dict['value'] = 'True' if attr_dict['value'] else 'False'
    elif attr_dict['type'] == u'localized':
        fill_localized_keys(attr_dict, ['value'], language)

    a = session.query(models.FieldAttr).filter(models.FieldAttr.field_id == field_id, models.FieldAttr.name == attr_name, models.FieldAttr.field_id == models.Field.id, models.Field.tid == tid).one_or_none()
    if a is None:
        a = models.db_forge_obj(session, models.FieldAttr, attr_dict)
    else:
        a.update(attr_dict)

    return a.id


def db_update_fieldattrs(session, tid, field_id, field_attrs, language):
    attrs_ids = [db_update_fieldattr(session, tid, field_id, attr_name, attr, language) for attr_name, attr in field_attrs.items()]

    if attrs_ids:
        ids_to_remove = session.query(models.FieldAttr.id).filter(models.FieldAttr.field_id == field_id,
                                                                  not_(models.FieldAttr.id.in_(attrs_ids)),
                                                                  models.FieldAttr.field_id == models.Field.id,
                                                                  models.Field.tid == tid)

        session.query(models.FieldAttr).filter(models.FieldAttr.id.in_(ids_to_remove.subquery())).delete(synchronize_session='fetch')


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

    :param session: the session on which perform queries.
    :param field_dict: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
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

        field_attrs = read_json_file(Settings.field_attrs_file)
        attrs = field_attrs.get(field.template_id, {})
        db_add_field_attrs(session, field.id, attrs)

    else:
        field = models.db_forge_obj(session, models.Field, field_dict)
        attrs = field_dict.get('attrs', [])
        options = field_dict.get('options', [])

        db_update_fieldattrs(session, tid, field.id, attrs, language)
        db_update_fieldoptions(session, tid, field.id, options, language)

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

    db_update_fieldattrs(session, tid, field.id, field_dict['attrs'], language)

    # make not possible to change field type
    field_dict['type'] = field.type
    if field_dict['instance'] != 'reference':
        db_update_fieldoptions(session, tid, field.id, field_dict['options'], language)

        # full update
        field.update(field_dict)

    else:
        # partial update
        field.update({
          'label': field_dict['label'],
          'hint': field_dict['hint'],
          'description': field_dict['description'],
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

    :param session: the session on which perform queries.
    :param field_id: the field_id of the field to update
    :param field: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
    """
    field = db_update_field(session, tid, field_id, field, language)

    return serialize_field(session, tid, field, language)


@transact
def delete_field(session, tid, field_id):
    """
    Delete the field object corresponding to field_id

    If the field has children, remove them as well.
    If the field is immediately attached to a step object, remove it as well.

    :param session: the session on which perform queries.
    :param field_id: the id corresponding to the field.
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

    :param session: the session on which perform queries.
    :param field_id: the parent id.
    :return: a generator of Field.id
    """
    field = session.query(models.Field).filter(models.Field.id == id).one_or_none()
    if field.fieldgroup_id is not None:
        yield field.fieldgroup_id
        yield fieldtree_ancestors(session, field.fieldgroup_id)


@transact
def get_fieldtemplate_list(session, tid, language):
    """
    Serialize all the field templates localizing their content depending on the language.

    :param session: the session on which perform queries.
    :param language: the language of the field definition dict
    :return: the current field list serialized.
    :rtype: list of dict
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
        Return a list of all the fields templates available.

        :return: the list of field templates registered on the node.
        :rtype: list
        """
        return get_fieldtemplate_list(self.request.tid, self.request.language)

    def post(self):
        """
        Create a new field template.
        """
        validator = requests.AdminFieldDesc if self.request.language is not None else requests.AdminFieldDescRaw

        request = self.validate_message(self.request.content.read(), validator)

        return create_field(self.request.tid, request, self.request.language)


class FieldTemplateInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, field_id):
        """
        Update a single field template's attributes.

        :param field_id:
        :rtype: FieldTemplateDesc
        :raises InputValidationError: if validation fails.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminFieldDesc)

        return update_field(self.request.tid,
                            field_id,
                            request,
                            self.request.language)

    def delete(self, field_id):
        """
        Delete a single field template.

        :param field_id:
        """
        return delete_field(self.request.tid, field_id)


class FieldsCollection(BaseHandler):
    """
    Operation to create a field

    /admin/fields
    """
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def post(self):
        """
        Create a new field.

        :return: the serialized field
        :rtype: AdminFieldDesc
        :raises InputValidationError: if validation fails.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminFieldDesc)

        return create_field(self.request.tid,
                            request,
                            self.request.language)


class FieldInstance(BaseHandler):
    """
    Operation to iterate over a specific requested Field

    /admin/fields
    """
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, field_id):
        """
        Update attributes of the specified step.

        :param field_id:
        :return: the serialized field
        :rtype: AdminFieldDesc
        :raises InputValidationError: if validation fails.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminFieldDesc)

        return update_field(self.request.tid,
                            field_id,
                            request,
                            self.request.language)

    def delete(self, field_id):
        """
        Delete a single field.

        :param field_id:
        :raises InputValidationError: if validation fails.
        """
        return delete_field(self.request.tid, field_id)
