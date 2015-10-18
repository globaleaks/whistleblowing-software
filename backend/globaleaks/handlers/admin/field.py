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
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.node import anon_serialize_field, anon_serialize_step, \
    get_public_context_list
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import transact, transact_ro
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import log


def associate_field(store, field, step=None, fieldgroup=None):
    """
    Associate a field to a specified step or fieldgroup

    :param store: the store on which perform queries.
    :param field: the field to be associated.
    :param step: the step to which associate the field
    :param fieldgroup: the fieldgroup to which associate the field
    """
    if step:
        if field.instance == 'template':
            raise errors.InvalidInputFormat("Cannot associate a field template to a step")

        step.children.add(field)

    if fieldgroup:
        if field.instance != fieldgroup.instance:
            raise errors.InvalidInputFormat("Cannot associate field templates with fields")

        ancestors = set(fieldtree_ancestors(store, field))

        if field.id in [field.template_id, fieldgroup.id] or \
           field.template_id == fieldgroup.id or \
           field.template_id in ancestors or \
           fieldgroup.id in ancestors:
             raise errors.InvalidInputFormat("Provided field association would cause recursion loop")

        fieldgroup.children.add(field)


def disassociate_field(store, field):
    """
    Disassociate a field from the eventually associated step or fieldgroup

    :param store: the store on which perform queries.
    :param field: the field to be deassociated.
    """
    field.step_id = None
    field.fieldgroud_id = None


def db_import_fields(store, step, fieldgroup, fields):
    for field in fields:
        f_attrs = copy.deepcopy(field['attrs'])
        f_options = copy.deepcopy(field['options'])
        f_children = copy.deepcopy(field['children'])

        del field['attrs'], field['options'], field['children']

        f = models.db_forge_obj(store, models.Field, field)

        for key, value in f_attrs.iteritems():
            value['name'] = key
            a = models.db_forge_obj(store, models.FieldAttr, value)
            f.attrs.add(a)

        for f_option in f_options:
            o = models.db_forge_obj(store, models.FieldOption, f_option)
            f.options.add(o)

        if (step):
            step.children.add(f)
        else:
            fieldgroup.children.add(f)

        if f_children:
            db_import_fields(store, None, f, f_children)


def db_update_fieldoption(store, fieldoption_id, option, language):
    fill_localized_keys(option, models.FieldOption.localized_strings, language)

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


def db_update_fieldattr(store, field_id, fieldattr):
    attr = store.find(models.FieldAttr, And(models.FieldAttr.field_id == field_id, models.FieldAttr.name == fieldattr['name'])).one()
    if not attr:
        attr = models.FieldAttr()

    fieldattr['field_id'] = field_id

    attr.update(fieldattr)

    store.add(attr)

    return attr.id


def db_update_fieldattrs(store, field_id, field_attrs, language):
    """
    """
    attrs_ids = []

    for name, value in field_attrs.iteritems():
        value['name'] = name
        if value['type'] == u'localized':
            fill_localized_keys(value, ['value'], language)

        attrs_ids.append(db_update_fieldattr(store, field_id, value))

    store.find(models.FieldAttr, And(models.FieldAttr.field_id == field_id, Not(In(models.FieldAttr.id, attrs_ids)))).remove()


def field_integrity_check(store, field):
    """
    Preliminar validations of field descriptor in relation to:
    - step_id
    - fieldgroup_id
    - instannce

    :param field: the field dict to be validated
    """
    step = None
    fieldgroup = None

    if field['instance'] != 'template' and (field['step_id'] == '' and field['fieldgroup_id'] == ''):
        raise errors.InvalidInputFormat("Each field should be a template or be associated to a step/fieldgroup")

    if field['instance'] != 'template' and (field['step_id'] != '' and field['fieldgroup_id'] != ''):
        raise errors.InvalidInputFormat("Cannot associate a field to both a step and a fieldgroup")

    if field['step_id'] != '':
        step = store.find(models.Step, models.Step.id == field['step_id']).one()
        if not step:
            raise errors.StepIdNotFound

    if field['fieldgroup_id'] != '':
        fieldgroup = store.find(models.Field, models.Field.id == field['fieldgroup_id']).one()
        if not fieldgroup:
            raise errors.FieldIdNotFound

    return field['instance'], step, fieldgroup


def db_create_field(store, field, language):
    """
    Create and add a new field to the store, then return the new serialized object.

    :param store: the store on which perform queries.
    :param field: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
    """
    _, step, fieldgroup = field_integrity_check(store, field)

    fill_localized_keys(field, models.Field.localized_strings, language)

    if field['instance'] != 'reference':
        field['template_id'] = None

    if field['step_id'] == '':
        field['step_id'] = None

    if field['fieldgroup_id'] == '':
        field['fieldgroup_id'] = None

    f = models.Field.new(store, field)

    if field['template_id'] is None:
        db_update_fieldattrs(store, f.id, field['attrs'], language)
        db_update_fieldoptions(store, f.id, field['options'], language)

    associate_field(store, f, step, fieldgroup)

    for c in field['children']:
        c['field_id'] = f.id
        field = db_create_field(store, c, language)
        f.children.add(field)

    return f


@transact
def create_field(store, field, language):
    """
    Transaction that perform db_create_field
    """
    f = db_create_field(store, field, language)

    return anon_serialize_field(store, f, language)


def db_update_field(store, field_id, field, language):
    f = models.Field.get(store, field_id)
    if not f:
        raise errors.FieldIdNotFound

    if not f.editable:
        raise errors.FieldNotEditable

    _, step, fieldgroup = field_integrity_check(store, field)

    fill_localized_keys(field, models.Field.localized_strings, language)

    if field['instance'] != 'reference':
        field['template_id'] = None

    if field['step_id'] == '':
        field['step_id'] = None

    if field['fieldgroup_id'] == '':
        field['fieldgroup_id'] = None

    try:
        # make not possible to change field type
        field['type'] = f.type

        if field['instance'] != 'reference':
            # children handling:
            #  - old children are cleared
            #  - new provided childrens are evaluated and added
            children = field['children']
            if len(children) and f.type != 'fieldgroup':
                raise errors.InvalidInputFormat("children can be associated only to fields of type fieldgroup")

            ancestors = set(fieldtree_ancestors(store, f))

            f.children.clear()
            for child in children:
                if child['id'] == f.id or child['id'] in ancestors:
                     raise errors.FieldIdNotFound

                c = db_update_field(store, child['id'], child, language)

                # remove current step/field fieldgroup/field association
                disassociate_field(store, c)

                f.children.add(c)

            db_update_fieldattrs(store, f.id, field['attrs'], language)
            db_update_fieldoptions(store, f.id, field['options'], language)

            # full update
            f.update(field)

        else:
            # partial update
            partial_update = {
              'x': field['x'],
              'y': field['y'],
              'width': field['width'],
              'stats_enabled': field['stats_enabled'],
              'multi_entry': field['multi_entry'],
              'required': field['required']
            }

            f.update(partial_update)

        # remove current step/field fieldgroup/field association
        disassociate_field(store, f)

        associate_field(store, f, step, fieldgroup)
    except Exception as dberror:
        log.err('Unable to update field: {e}'.format(e=dberror))
        raise errors.InvalidInputFormat(dberror)

    return f


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

    return anon_serialize_field(store, field, language)


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

    return anon_serialize_field(store, field, language)


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

    if not field.editable:
        raise errors.FieldNotEditable

    field.delete(store)


def fieldtree_ancestors(store, field):
    """
    Given a field_id, recursively extract its parents.

    :param store: the store on which perform queries.
    :param field_id: the parent id.
    :return: a generator of Field.id
    """
    if field.fieldgroup:
        yield field.fieldgroup.id
        yield fieldtree_ancestors(store, field.fieldgroup)


@transact_ro
def get_fieldtemplates_list(store, language):
    """
    Serialize all the field templates localizing their content depending on the language.

    :param store: the store on which perform queries.
    :param language: the language of the field definition dict
    :return: the current field list serialized.
    :rtype: list of dict
    """
    ret = []

    for f in store.find(models.Field, models.Field.instance == u'template'):
        #if not store.find(models.FieldField, models.FieldField.child_id == f.id).one():
        ret.append(anon_serialize_field(store, f, language))

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
        response = yield get_fieldtemplates_list(self.request.language)
        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new field template.

        """
        request = self.validate_message(self.request.body,
                                        requests.AdminFieldDesc)

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

        # get the updated list of contexts, and update the cache
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

        # get the updated list of contexts, and update the cache
        GLApiCache.invalidate('contexts')

        self.set_status(200)
