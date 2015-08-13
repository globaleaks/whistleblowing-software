# -*- coding: UTF-8
"""
Implementation of the code executed when an HTTP client reach /admin/fields URI.
"""
from __future__ import unicode_literals

import json

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


def get_field_association(store, field_id):
    """
    Return a boolean tuple representing the field association (step, fieldgroup) [true, false]

    :param store: the store on which perform queries.
    """
    ret1 = None
    ret2 = None

    sf = store.find(models.StepField, models.StepField.field_id == field_id).one()
    if sf:
        ret1 = sf.step_id

    ff = store.find(models.FieldField, models.FieldField.child_id == field_id).one()
    if ff:
        ret2 = ff.parent_id

    return ret1, ret2


def associate_field(store, field, step=None, fieldgroup=None):
    """
    Associate a field to a specified step or fieldgroup

    :param store: the store on which perform queries.
    """
    if step:
        if field.is_template:
            raise errors.InvalidInputFormat("Cannot associate a field template to a step")

        step.children.add(field)

    if fieldgroup:
        if field.is_template != fieldgroup.is_template:
            raise errors.InvalidInputFormat("Cannot associate field templates with fields")

        fieldgroup.children.add(field)


def disassociate_field(store, field_id):
    """
    Disassociate a field from the eventually associated step or fieldgroup

    :param store: the store on which perform queries.
    """
    sf = store.find(models.StepField, models.StepField.field_id == field_id).one()
    if sf:
        store.remove(sf)
    ff = store.find(models.FieldField, models.FieldField.child_id == field_id).one()
    if ff:
        store.remove(ff)


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

        print value
        attrs_ids.append(db_update_fieldattr(store, field_id, value))

    store.find(models.FieldAttr, And(models.FieldAttr.field_id == field_id, Not(In(models.FieldAttr.id, attrs_ids)))).remove()


def field_integrity_check(store, field):
    """
    Verify the congruence of step_id, fieldgroup_id and is_template attrs in field dict

    :param field: the field dict to be validated
    """
    is_template = field['is_template']
    step_id = field.get('step_id')
    fieldgroup_id = field.get('fieldgroup_id')

    step = None
    fieldgroup = None

    if not is_template and \
       (step_id == '' or step_id is None) and \
       (fieldgroup_id == '' or fieldgroup_id is None):
        raise errors.InvalidInputFormat("Each field should be a template or be associated to a step/fieldgroup")

    if not is_template:
        if (step_id == '' or step_id is None) and \
            (fieldgroup_id == '' or fieldgroup_id is None):
            raise errors.InvalidInputFormat("Cannot associate a field to both a step and a fieldgroup")

    if step_id:
        step = store.find(models.Step, models.Step.id == step_id).one()
        if not step:
            raise errors.StepIdNotFound

    if fieldgroup_id:
        fieldgroup = store.find(models.Field, models.Field.id == fieldgroup_id).one()
        if not fieldgroup:
            raise errors.FieldIdNotFound

    return is_template, step, fieldgroup


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
    f = models.Field.new(store, field)
    db_update_fieldattrs(store, f.id, field['attrs'], language)
    db_update_fieldoptions(store, f.id, field['options'], language)

    associate_field(store, f, step, fieldgroup)

    ancestors = set(fieldtree_ancestors(store, f.id))

    for child in field['children']:
        if child['id'] == f.id or child['id'] in ancestors:
            raise errors.InvalidInputFormat

        db_update_field(store, child['id'], child, language)

    return f


def db_create_field_from_template(store, field, language):
    """
    Create and add a new field to the store starting from a template,
    then return the new serialized object.

    :param store: the store on which perform queries.
    :param field: the field definition dict
    :param language: the language of the field definition dict
    :return: a serialization of the object
    """
    _, step, fieldgroup = field_integrity_check(store, field)

    template = store.find(models.Field, models.Field.id == field['template_id']).one()
    if not template:
        raise errors.InvalidInputFormat("The specified template id %s does not exist" %
                                        field.get('template_id'))
    f = template.copy(store, False)

    associate_field(store, f, step, fieldgroup)

    return f


@transact
def create_field(store, field, language):
    """
    Transaction that perform db_create_field
    """
    f = db_create_field(store, field, language)

    return anon_serialize_field(store, f, language)


@transact
def create_field_from_template(store, field, language):
    """
    Transaction that perform db_create_field_from_template
    """
    f = db_create_field_from_template(store, field, language)

    return anon_serialize_field(store, f, language)


def db_update_field(store, field_id, field, language):
    _, step, fieldgroup = field_integrity_check(store, field)

    fill_localized_keys(field, models.Field.localized_strings, language)

    try:
        f = models.Field.get(store, field_id)
        if not f:
            raise errors.FieldIdNotFound

        f.update(field)

        # children handling:
        #  - old children are cleared
        #  - new provided childrens are evaluated and added
        children = field['children']
        if len(children) and f.type != 'fieldgroup':
            raise errors.InvalidInputFormat("children can be associated only to fields of type fieldgroup")

        ancestors = set(fieldtree_ancestors(store, f.id))

        f.children.clear()
        for child in children:
            if child['id'] == f.id or child['id'] in ancestors:
                raise errors.FieldIdNotFound

            c = db_update_field(store, child['id'], child, language)

            # remove current step/field fieldgroup/field association
            disassociate_field(store, c.id)

            f.children.add(c)

        db_update_fieldattrs(store, f.id, field['attrs'], language)
        db_update_fieldoptions(store, f.id, field['options'], language)

        # remove current step/field fieldgroup/field association
        disassociate_field(store, field_id)

        associate_field(store, f, step, fieldgroup)

        return f

    except Exception as dberror:
        log.err('Unable to update field: {e}'.format(e=dberror))
        raise errors.InvalidInputFormat(dberror)


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
def get_field(store, field_id, is_template, language):
    """
    Serialize a specified field

    :param store: the store on which perform queries.
    :param field_id: the id corresponding to the field.
    :param is_template: a boolean specifying if the requested field needs to be a template
    :param language: the language in which to localize data
    :return: the currently configured field.
    :rtype: dict
    """
    field = store.find(models.Field, And(models.Field.id == field_id, models.Field.is_template == is_template)).one()
    if not field:
        raise errors.FieldIdNotFound

    return anon_serialize_field(store, field, language)


@transact
def delete_field(store, field_id, is_template):
    """
    Delete the field object corresponding to field_id

    If the field has children, remove them as well.
    If the field is immediately attached to a step object, remove it as well.

    :param store: the store on which perform queries.
    :param field_id: the id corresponding to the field.
    :param is_template: a boolean specifying if the requested field needs to be a template
    :raises FieldIdNotFound: if no such field is found.
    """
    field = store.find(models.Field, And(models.Field.id == field_id, models.Field.is_template == is_template)).one()
    if not field:
        raise errors.FieldIdNotFound

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
            for grandpa in fieldtree_ancestors(store, parent.parent_id): yield grandpa


@transact_ro
def get_field_list(store, is_template, language):
    """
    Serialize all the root fields (templates or not templates)
    localizing their content depending on the language.

    :param store: the store on which perform queries.
    :param language: the language of the field definition dict
    :return: the current field list serialized.
    :rtype: list of dict
    """
    ret = []

    for f in store.find(models.Field, models.Field.is_template == is_template):
        if not store.find(models.FieldField, models.FieldField.child_id == f.id).one():
            ret.append(anon_serialize_field(store, f, language))

    return ret


def db_create_step(store, step, language):
     """
     Create the specified step
 
     :param store: the store on which perform queries.
     :param language: the language of the specified steps.
     """
     fill_localized_keys(step, models.Step.localized_strings, language)

     s = models.Step.new(store, step)
     for f in step['children']:
         field = models.Field.get(store, f['id'])
         if not field:
             log.err("Creation error: unexistent field can't be associated")
             raise errors.FieldIdNotFound

         db_update_field(f['id'], f, language)

     return s


@transact
def create_step(store, step, language):
    """
    Transaction that perform db_create_step
    """
    s = db_create_step(store, step, language)

    return anon_serialize_step(store, s, language)


@transact
def update_step(store, step_id, request, language):
    """
    Update the specified step with the details.
    raises :class:`globaleaks.errors.StepIdNotFound` if the step does
    not exist.

    :param store: the store on which perform queries.
    :param step_id: the step_id of the step to update
    :param request: the step definition dict
    :param language: the language of the step definition dict
    :return: a serialization of the object
    """
    step = models.Step.get(store, step_id)
    try:
        if not step:
            raise errors.StepIdNotFound

        fill_localized_keys(request, models.Step.localized_strings, language)

        step.update(request)

    except Exception as dberror:
        log.err('Unable to update step: {e}'.format(e=dberror))
        raise errors.InvalidInputFormat(dberror)

    return anon_serialize_step(store, step, language)


@transact_ro
def get_step(store, step_id, language):
    """
    Serialize the specified step

    :param store: the store on which perform queries.
    :param step_id: the id corresponding to the step.
    :param language: the language in which to localize data
    :return: the currently configured step.
    :rtype: dict
    """
    step = store.find(models.Step, models.Step.id == step_id).one()
    if not step:
        raise errors.StepIdNotFound

    return anon_serialize_step(store, step, language)


@transact
def delete_step(store, step_id):
    """
    Delete the step object corresponding to step_id

    If the step has children, remove them as well.

    :param store: the store on which perform queries.
    :param step_id: the id corresponding to the step.
    :raises StepIdNotFound: if no such step is found.
    """
    step = store.find(models.Step, models.Step.id == step_id).one()
    if not step:
        raise errors.StepIdNotFound

    step.delete(store)


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
        response = yield get_field_list(True, self.request.language)
        self.set_status(200)
        self.finish(response)


class FieldTemplateCreate(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new field template.

        """
        request = self.validate_message(self.request.body,
                                        requests.FieldTemplateDesc)

        # enforce difference between /admin/field and /admin/fieldtemplate
        request['is_template'] = True

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
        response = yield get_field(field_id, True, self.request.language)
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
                                        requests.FieldTemplateDesc)

        # enforce difference between /admin/field and /admin/fieldtemplate
        request['is_template'] = True

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
        yield delete_field(field_id, True)
        self.set_status(200)


class FieldCreate(BaseHandler):
    """
    Operation to create a field

    /admin/field
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new field.

        :return: the serialized field
        :rtype: FieldDesc
        :raises InvalidInputFormat: if validation fails.
        """
        try:
            tmp = json.loads(self.request.body)
        except ValueError:
            raise errors.InvalidInputFormat("Invalid JSON format")

        if isinstance(tmp, dict) and 'template_id' in tmp:
            request = self.validate_message(self.request.body,
                                            requests.FieldFromTemplateDesc)

            # enforce difference between /admin/field and /admin/fieldtemplate
            request['is_template'] = False
            response = yield create_field_from_template(request, self.request.language)

        else:
            request = self.validate_message(self.request.body,
                                            requests.FieldDesc)

            # enforce difference between /admin/field and /admin/fieldtemplate
            request['is_template'] = False
            response = yield create_field(request, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')

        self.set_status(201)
        self.finish(response)


class FieldInstance(BaseHandler):
    """
    Operation to iterate over a specific requested Field

    /admin/field
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, field_id):
        """
        Get the field identified by field_id

        :param field_id:
        :return: the serialized field
        :rtype: FieldDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_field(field_id, False, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
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
        :rtype: FieldDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.FieldDesc)

        # enforce difference between /admin/field and /admin/fieldtemplate
        request['is_template'] = False

        response = yield update_field(field_id, request, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
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
        yield delete_field(field_id, False)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')

        self.set_status(200)


class StepCreate(BaseHandler):
    """
    Operation to create a step

    /admin/step
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new step.

        :return: the serialized step
        :rtype: StepDesc
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.StepDesc)

        response = yield create_step(request, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(201)
        self.finish(response)


class StepInstance(BaseHandler):
    """
    Operation to iterate over a specific requested Step

    /admin/step
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, step_id):
        """
        Get the step identified by step_id

        :param step_id:
        :return: the serialized step
        :rtype: StepDesc
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_step(step_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, step_id):
        """
        Update attributes of the specified step

        :param step_id:
        :return: the serialized step
        :rtype: StepDesc
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.StepDesc)

        response = yield update_step(step_id, request, self.request.language)

        GLApiCache.invalidate('contexts')

        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, step_id):
        """
        Delete the specified step.

        :param step_id:
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        yield delete_step(step_id)

        GLApiCache.invalidate('contexts')

        self.set_status(200)
