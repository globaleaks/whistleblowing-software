# -*- coding: utf-8
#
#   /admin/fields
#   *****
# Implementation of the code executed on handler /admin/fields
#
from storm.expr import And, Not, In

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import serialize_field
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.utils.structures import fill_localized_keys


def db_update_fieldoption(store, tid, field, fieldoption_id, option_dict, language, idx):
    option_dict['tid'] = tid
    option_dict['field_id'] = field.id

    fill_localized_keys(option_dict, models.FieldOption.localized_keys, language)

    o = None
    if fieldoption_id is not None:
        o = store.find(models.FieldOption, id=fieldoption_id).one()

    if o is None:
        o = models.db_forge_obj(store, models.FieldOption, option_dict)
    else:
        o.update(option_dict)

    o.presentation_order = idx

    return o.id


def db_update_fieldoptions(store, tid, field, options, language):
    """
    Update options

    :param store: the store on which perform queries.
    :param field_id: the field_id on wich bind the provided options
    :param language: the language of the option definition dict
    """
    options_ids = [db_update_fieldoption(store, tid, field, option['id'], option, language, idx) for idx, option in enumerate(options)]

    store.find(models.FieldOption, And(models.FieldOption.field_id == field.id, Not(In(models.FieldOption.id, options_ids)))).remove()


def db_update_fieldattr(store, tid, field, attr_name, attr_dict, language):
    attr_dict['name'] = attr_name
    attr_dict['field_id'] = field.id
    attr_dict['tid'] = tid

    if attr_dict['type'] == 'bool':
        attr_dict['value'] = 'True' if attr_dict['value'] else 'False'
    elif attr_dict['type'] == u'localized':
        fill_localized_keys(attr_dict, ['value'], language)

    a = store.find(models.FieldAttr, And(models.FieldAttr.field_id == field.id, models.FieldAttr.name == attr_name)).one()
    if not a:
        a = models.db_forge_obj(store, models.FieldAttr, attr_dict)
    else:
        a.update(attr_dict)

    return a.id


def db_update_fieldattrs(store, tid, field, field_attrs, language):
    attrs_ids = [db_update_fieldattr(store, tid, field, attr_name, attr, language) for attr_name, attr in field_attrs.items()]

    store.find(models.FieldAttr, And(models.FieldAttr.field_id == field.id, Not(In(models.FieldAttr.id, attrs_ids)))).remove()


def db_create_field(store, tid, field_dict, language):
    """
    Create and add a new field to the store, then return the new serialized object.

    :param store: the store on which perform queries.
    :param field_dict: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
    """
    field_dict['tid'] = tid

    fill_localized_keys(field_dict, models.Field.localized_keys, language)

    if field_dict.get('fieldgroup_id', ''):
        ancestors = set(fieldtree_ancestors(store, field_dict['tid'], field_dict['fieldgroup_id']))

        if field_dict['id'] == field_dict['fieldgroup_id'] or field_dict['id'] in ancestors:
            raise errors.InvalidInputFormat("Provided field association would cause recursion loop")

    field = models.db_forge_obj(store, models.Field, field_dict)

    if field.template_id is not None:
        # special handling of the whistleblower_identity field
        if field.template_id == 'whistleblower_identity':
            if field.step_id is not None:
                questionnaire = store.find(models.Questionnaire,
                                           models.Field.id == field.id,
                                           models.Field.step_id == models.Step.id,
                                           models.Step.questionnaire_id == models.Questionnaire.id).one()

                if questionnaire.enable_whistleblower_identity is False:
                    questionnaire.enable_whistleblower_identity = True
                else:
                    raise errors.InvalidInputFormat("Whistleblower identity field already present")
            else:
                raise errors.InvalidInputFormat("Cannot associate whistleblower identity field to a fieldgroup")

    else:
        attrs = field_dict.get('attrs', [])
        options = field_dict.get('options', [])

        for key, value in attrs.items():
            value['tid'] = field.tid

        for obj in options:
            obj['tid'] = field.tid

        db_update_fieldattrs(store, tid, field, attrs, language)
        db_update_fieldoptions(store, tid, field, options, language)

    if field.instance != 'reference':
        for c in field_dict.get('children', []):
            c['tid'] = field.tid
            c['fieldgroup_id'] = field.id
            db_create_field(store, tid, c, language)

    return field


@transact
def create_field(store, tid, field_dict, language):
    """
    Transaction that perform db_create_field
    """
    field = db_create_field(store, tid, field_dict, language)

    return serialize_field(store, field, language)


def db_update_field(store, tid, field_id, field_dict, language):
    field = models.db_get(store, models.Field, tid=tid, id=field_id)

    # make not possible to change field type
    field_dict['type'] = field.type
    if field_dict['instance'] != 'reference':
        fill_localized_keys(field_dict, models.Field.localized_keys, language)

        db_update_fieldattrs(store, tid, field, field_dict['attrs'], language)
        db_update_fieldoptions(store, tid, field, field_dict['options'], language)

        # full update
        field.update(field_dict)

    else:
        # partial update
        field.update({
          'x': field_dict['x'],
          'y': field_dict['y'],
          'width': field_dict['width'],
          'multi_entry': field_dict['multi_entry']
        })

    return field


@transact
def update_field(store, tid, field_id, field, language):
    """
    Update the specified field with the details.

    :param store: the store on which perform queries.
    :param field_id: the field_id of the field to update
    :param field: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
    """
    field = db_update_field(store, tid, field_id, field, language)

    return serialize_field(store, field, language)


@transact
def delete_field(store, tid, field_id):
    """
    Delete the field object corresponding to field_id

    If the field has children, remove them as well.
    If the field is immediately attached to a step object, remove it as well.

    :param store: the store on which perform queries.
    :param field_id: the id corresponding to the field.
    """
    field = models.db_get(store, models.Field, tid=tid, id=field_id)

    if not field.editable:
        raise errors.FieldNotEditable

    if field.instance == 'template':
        if store.find(models.Field, models.Field.template_id == field.id).count():
            raise errors.InvalidInputFormat("Cannot remove the field template as it is used by one or more questionnaires")


    if field.template_id == 'whistleblower_identity' and field.step_id is not None:
        store.find(models.Questionnaire,
                   models.Step.id == field.step_id,
                   models.Questionnaire.id == models.Step.questionnaire_id).set(enable_whistleblower_identity = False)

    store.remove(field)


def fieldtree_ancestors(store, tid, id):
    """
    Given a field_id, recursively extract its parents.

    :param store: the store on which perform queries.
    :param field_id: the parent id.
    :return: a generator of Field.id
    """
    field = store.find(models.Field, tid=tid, id=id).one()
    if field.fieldgroup_id is not None:
        yield field.fieldgroup_id
        yield fieldtree_ancestors(store, field.tid, field.fieldgroup_id)


@transact
def get_fieldtemplate_list(store, tid, language):
    """
    Serialize all the field templates localizing their content depending on the language.

    :param store: the store on which perform queries.
    :param language: the language of the field definition dict
    :return: the current field list serialized.
    :rtype: list of dict
    """
    templates = store.find(models.Field, tid=tid, instance=u'template', fieldgroup_id=None)

    return [serialize_field(store, f, language) for f in templates]


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
        :raises InvalidInputFormat: if validation fails.
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
        :raises InvalidInputFormat: if validation fails.
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
        :raises InvalidInputFormat: if validation fails.
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
        :raises InvalidInputFormat: if validation fails.
        """
        return delete_field(self.request.tid, field_id)
