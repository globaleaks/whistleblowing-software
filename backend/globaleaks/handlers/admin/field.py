# -*- coding: UTF-8
#
#   /admin/fields
#   *****
# Implementation of the code executed on handler /admin/fields
#
import copy

from storm.expr import And, Not, In

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.node import serialize_field
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import log


def associate_field(store, field, template=None, step=None, fieldgroup=None):
    """
    Associate a field to a specified step or fieldgroup

    :param store: the store on which perform queries
    :param field: the field to be associated
    :param template: the template to which bind the field
    :param step: the step to which associate the field
    :param fieldgroup: the fieldgroup to which associate the field
    """
    if template:
        if field.instance != 'reference':
             raise errors.InvalidInputFormat("Only fields of kind reference can be binded to a template")

        field.template_id = template.id

    if step:
        if field.instance == 'template':
            raise errors.InvalidInputFormat("Cannot associate a field template to a step")

        step.children.add(field)

    if fieldgroup:
        if field.instance == 'template' and fieldgroup.instance != 'template':
            raise errors.InvalidInputFormat("Cannot associate field template to a field")

        ancestors = set(fieldtree_ancestors(store, fieldgroup.id))

        if field.id == fieldgroup.id or field.id in ancestors:
            raise errors.InvalidInputFormat("Provided field association would cause recursion loop")

        fieldgroup.children.add(field)


def disassociate_field(field):
    """
    Disassociate a field from the eventually associated step or fieldgroup

    :param store: the store on which perform queries.
    :param field: the field to be deassociated.
    """
    field.steps.clear()
    field.fieldgroups.clear()


def db_import_fields(store, step, fieldgroup, fields):
    for field in fields:
        f_attrs = copy.deepcopy(field['attrs'])
        f_options = copy.deepcopy(field['options'])
        f_children = copy.deepcopy(field['children'])

        del field['attrs'], field['options'], field['children']

        f = models.db_forge_obj(store, models.Field, field)

        for attr in f_attrs:
            f_attrs[attr]['name'] = attr
            f.attrs.add(models.db_forge_obj(store, models.FieldAttr, f_attrs[attr]))

        for option in f_options:
            f.options.add(models.db_forge_obj(store, models.FieldOption, option))

        if (step):
            step.children.add(f)
        else:
            fieldgroup.children.add(f)

        if f_children:
            db_import_fields(store, None, f, f_children)


def db_update_fieldoption(store, fieldoption_id, option, language):
    fill_localized_keys(option, models.FieldOption.localized_keys, language)

    if fieldoption_id is not None:
        o = store.find(models.FieldOption, models.FieldOption.id == fieldoption_id).one()
    else:
        o = None

    if o is None:
        o = models.FieldOption()
        store.add(o)

    o.update(option)

    for activated_field in option['activated_fields']:
        o.activated_fields.add(store.find(models.Field, models.Field.id == activated_field))

    for activated_step in option['activated_steps']:
        o.activated_steps.add(store.find(models.Step, models.Step.id == activated_step))

    return o.id


def db_update_fieldoptions(store, field_id, options, language):
    """
    Update options

    :param store: the store on which perform queries.
    :param field_id: the field_id on wich bind the provided options
    :param language: the language of the option definition dict
    """
    options_ids = []

    for option in options:
        option['field_id'] = field_id
        options_ids.append(db_update_fieldoption(store, unicode(option['id']), option, language))

    store.find(models.FieldOption, And(models.FieldOption.field_id == field_id, Not(In(models.FieldOption.id, options_ids)))).remove()


def db_update_fieldattr(store, field_id, attr_name, attr_dict, language):
    attr = store.find(models.FieldAttr, And(models.FieldAttr.field_id == field_id, models.FieldAttr.name == attr_name)).one()
    if not attr:
        attr = models.FieldAttr()

    attr_dict['name'] = attr_name
    attr_dict['field_id'] = field_id

    if attr_dict['type'] == 'bool':
        attr_dict['value'] = 'True' if attr_dict['value'] == True else 'False'
    elif attr_dict['type'] == u'localized':
        fill_localized_keys(attr_dict, ['value'], language)

    attr.update(attr_dict)

    store.add(attr)

    return attr.id


def db_update_fieldattrs(store, field_id, field_attrs, language):
    attrs_ids = [db_update_fieldattr(store, field_id, attr_name, attr, language) for attr_name, attr in field_attrs.iteritems()]

    store.find(models.FieldAttr, And(models.FieldAttr.field_id == field_id, Not(In(models.FieldAttr.id, attrs_ids)))).remove()


def field_integrity_check(store, field):
    """
    Preliminar validations of field descriptor in relation to:
    - step_id
    - fieldgroup_id
      template_id
    - instance type

    :param field: the field dict to be validated
    """
    template = None
    step = None
    fieldgroup = None

    if field['instance'] != 'template' and (field['step_id'] == '' and field['fieldgroup_id'] == ''):
        raise errors.InvalidInputFormat("Each field should be a template or be associated to a step/fieldgroup")

    if field['instance'] != 'template' and (field['step_id'] != '' and field['fieldgroup_id'] != ''):
        raise errors.InvalidInputFormat("Cannot associate a field to both a step and a fieldgroup")

    if field['template_id'] != '':
        template = store.find(models.Field, models.Field.id == field['template_id']).one()
        if not template:
            raise errors.FieldIdNotFound

    if field['step_id'] != '':
        step = store.find(models.Step, models.Step.id == field['step_id']).one()
        if not step:
            raise errors.StepIdNotFound

    if field['fieldgroup_id'] != '':
        fieldgroup = store.find(models.Field, models.Field.id == field['fieldgroup_id']).one()
        if not fieldgroup:
            raise errors.FieldIdNotFound

    return field['instance'], template, step, fieldgroup


def db_create_field(store, field_dict, language):
    """
    Create and add a new field to the store, then return the new serialized object.

    :param store: the store on which perform queries.
    :param field: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
    """
    _, template, step, fieldgroup = field_integrity_check(store, field_dict)

    fill_localized_keys(field_dict, models.Field.localized_keys, language)

    field = models.Field.new(store, field_dict)

    associate_field(store, field, template, step, fieldgroup)

    if field.template:
        # special handling of the whistleblower_identity field
        if field.template.key == 'whistleblower_identity':
            step = field.steps.one()
            if step:
                if not step.context.enable_whistleblower_identity:
                    step.context.enable_whistleblower_identity = True
                else:
                    raise errors.InvalidInputFormat("Whistleblower identity field already present")
            else:
                raise errors.InvalidInputFormat("Cannot associate whistleblower identity field to a fieldgroup")

    else:
        db_update_fieldattrs(store, field.id, field_dict['attrs'], language)
        db_update_fieldoptions(store, field.id, field_dict['options'], language)

    for c in field_dict['children']:
        c['fieldgroup_id'] = field.id
        db_create_field(store, c, language)

    return field


@transact
def create_field(store, field_dict, language, import_export=None):
    """
    Transaction that perform db_create_field
    """
    field = db_create_field(store, field_dict, language if import_export != 'import' else None)

    return serialize_field(store, field, language if import_export != 'export' else None)


def db_update_field(store, field_id, field_dict, language):
    field = models.Field.get(store, field_id)
    if not field:
        raise errors.FieldIdNotFound

    # To be uncommented upon completion of fields implementaion
    # if not field.editable:
    #     raise errors.FieldNotEditable

    _, template, step, fieldgroup = field_integrity_check(store, field_dict)

    try:
        # make not possible to change field type
        field_dict['type'] = field.type

        if field_dict['instance'] != 'reference':
            fill_localized_keys(field_dict, models.Field.localized_keys, language)

            # children handling:
            #  - old children are cleared
            #  - new provided childrens are evaluated and added
            children = field_dict['children']
            if len(children) and field.type != 'fieldgroup':
                raise errors.InvalidInputFormat("children can be associated only to fields of type fieldgroup")

            ancestors = set(fieldtree_ancestors(store, field.id))

            field.children.clear()
            for child in children:
                if child['id'] == field.id or child['id'] in ancestors:
                    raise errors.FieldIdNotFound

                c = db_update_field(store, child['id'], child, language)

                # remove current step/field fieldgroup/field association
                disassociate_field(c)

                field.children.add(c)

            db_update_fieldattrs(store, field.id, field_dict['attrs'], language)
            db_update_fieldoptions(store, field.id, field_dict['options'], language)

            # full update
            field.update(field_dict)

        else:
            # partial update
            partial_update = {
              'x': field_dict['x'],
              'y': field_dict['y'],
              'width': field_dict['width'],
              'multi_entry': field_dict['multi_entry']
            }

            field.update(partial_update)

        # remove current step/field fieldgroup/field association
        disassociate_field(field)

        associate_field(store, field, template, step, fieldgroup)
    except Exception as dberror:
        log.err('Unable to update field: {e}'.format(e=dberror))
        raise errors.InvalidInputFormat(dberror)

    return field


@transact
def update_field(store, field_id, field, language):
    """
    Update the specified field with the details.
    raises :class:`globaleaks.errors.FieldIdNotFound` if the field does
    not exist.

    :param store: the store on which perform queries.
    :param field_id: the field_id of the field to update
    :param field: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
    """
    field = db_update_field(store, field_id, field, language)

    return serialize_field(store, field, language)


@transact_ro
def get_field(store, field_id, language):
    """
    Serialize a specified field

    :param store: the store on which perform queries.
    :param field_id: the id corresponding to the field.
    :param language: the language in which to localize data
    :return: the currently configured field.
    :rtype: dict
    """
    field = store.find(models.Field, models.Field.id == field_id).one()
    if not field:
        raise errors.FieldIdNotFound

    return serialize_field(store, field, language)


@transact
def delete_field(store, field_id):
    """
    Delete the field object corresponding to field_id

    If the field has children, remove them as well.
    If the field is immediately attached to a step object, remove it as well.

    :param store: the store on which perform queries.
    :param field_id: the id corresponding to the field.
    :raises FieldIdNotFound: if no such field is found.
    """
    field = store.find(models.Field, models.Field.id == field_id).one()
    if not field:
        raise errors.FieldIdNotFound

    # To be uncommented upon completion of fields implementaion
    # if not field.editable:
    #     raise errors.FieldNotEditable

    if field.instance == 'template':
        if store.find(models.Field, models.Field.template_id == field.id).count():
            raise errors.InvalidInputFormat("Cannot remove the field template as it is used by one or more questionnaires")


    if field.template:
        # special handling of the whistleblower_identity field
        if field.template.key == 'whistleblower_identity':
            step = field.steps.one()
            if step:
                step.context.enable_whistleblower_identity = False

    field.delete(store)


def fieldtree_ancestors(store, field_id):
    """
    Given a field_id, recursively extract its parents.

    :param store: the store on which perform queries.
    :param field_id: the parent id.
    :return: a generator of Field.id
    """
    parents = store.find(models.FieldField, models.FieldField.child_id == field_id)
    for parent in parents:
        if parent.parent_id != field_id:
            yield parent.parent_id
            for grandpa in fieldtree_ancestors(store, parent.parent_id):
                yield grandpa


@transact_ro
def get_fieldtemplate_list(store, language):
    """
    Serialize all the field templates localizing their content depending on the language.

    :param store: the store on which perform queries.
    :param language: the language of the field definition dict
    :return: the current field list serialized.
    :rtype: list of dict
    """
    ret = []

    for f in store.find(models.Field, models.Field.instance == u'template'):
        if not store.find(models.FieldField, models.FieldField.child_id == f.id).one():
            ret.append(serialize_field(store, f, language))

    return ret


class FieldTemplatesCollection(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return a list of all the fields templates available.

        :return: the list of field templates registered on the node.
        :rtype: list
        """
        response = yield get_fieldtemplate_list(self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new field template.
        """
        validator = requests.AdminFieldDesc if self.request.language is not None else requests.AdminFieldDescRaw

        request = self.validate_message(self.request.body, validator)

        response = yield create_field(request, self.request.language)

        self.set_status(201)
        self.finish(response)


class FieldTemplateInstance(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, field_id):
        """
        Get the field identified by field_id

        :param field_id:
        :rtype: FieldTemplateDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_field(field_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, field_id):
        """
        Update a single field template's attributes.

        :param field_id:
        :rtype: FieldTemplateDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminFieldDesc)

        response = yield update_field(field_id, request, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, field_id):
        """
        Delete a single field template.

        :param field_id:
        :raises FieldIdNotFound: if there is no field with such id.
        """
        yield delete_field(field_id)

        GLApiCache.invalidate('contexts')

        self.set_status(200)


class FieldCollection(BaseHandler):
    """
    Operation to create a field

    /admin/fields
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new field.

        :return: the serialized field
        :rtype: AdminFieldDesc
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminFieldDesc)

        response = yield create_field(request, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(201)
        self.finish(response)


class FieldInstance(BaseHandler):
    """
    Operation to iterate over a specific requested Field

    /admin/fields
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, field_id):
        """
        Get the field identified by field_id

        :param field_id:
        :return: the serialized field
        :rtype: AdminFieldDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_field(field_id, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, field_id):
        """
        Update attributes of the specified step.

        :param field_id:
        :return: the serialized field
        :rtype: AdminFieldDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminFieldDesc)

        response = yield update_field(field_id, request, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, field_id):
        """
        Delete a single field.

        :param field_id:
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        yield delete_field(field_id)

        GLApiCache.invalidate('contexts')

        self.set_status(200)
