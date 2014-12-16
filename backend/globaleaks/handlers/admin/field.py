# -*- coding: UTF-8
"""
Implementation of the code executed when an HTTP client reach /admin/fields URI.
"""
from __future__ import unicode_literals

import json
from storm.exceptions import DatabaseError
from storm.expr import And
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler, GLApiCache
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.node import anon_serialize_field, anon_serialize_option, \
    get_field_option_localized_keys, get_public_context_list
from globaleaks.rest import errors, requests
from globaleaks.settings import transact, transact_ro
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log

def get_field_association(store, field_id):
    ret1 = None
    ret2 = None

    sf = store.find(models.StepField, models.StepField.field_id == field_id).one()
    if sf:
        ret1 = sf.step_id

    ff = store.find(models.FieldField, models.FieldField.child_id == field_id).one()
    if ff:
        ret2 = ff.parent_id

    return ret1, ret2

def associate_field(store, field, step_id=None, fieldgroup_id=None):
    if step_id:
        if field.is_template:
            raise errors.InvalidInputFormat("Cannot associate a field template to a step")

        step = store.find(models.Step, models.Step.id == step_id).one()
        step.children.add(field)

    elif fieldgroup_id:
        fieldgroup = store.find(models.Field, models.Field.id == fieldgroup_id).one()

        if field.is_template != fieldgroup.is_template:
            raise errors.InvalidInputFormat("Cannot associate field templates with fields")

        fieldgroup.children.add(field)

def disassociate_field(store, field_id):
    sf = store.find(models.StepField, models.StepField.field_id == field_id).one()
    if sf:
        store.remove(sf)
    ff = store.find(models.FieldField, models.FieldField.child_id == field_id).one()
    if ff:
        store.remove(ff)

def db_update_options(store, field_id, options, language):
    """
    Update options
    """
    field = models.Field.get(store, field_id)
    if field is None:
        raise errors.FieldIdNotFound

    old_options = store.find(models.FieldOption,
                             models.FieldOption.field_id == field_id)

    indexed_old_options = {}
    for o in old_options:
        indexed_old_options[o.id] = o

    new_options = []
    n = 1
    for option in options:
        opt_dict = {}
        opt_dict['field_id'] = field_id
        opt_dict['number'] = n

        keys = get_field_option_localized_keys(field.type)
        fill_localized_keys(option['attrs'], keys, language)
        opt_dict['attrs'] = option['attrs']

        # check for reuse (needed to keep translations)
        if 'id' in option and option['id'] in indexed_old_options:
           o = indexed_old_options[option['id']]
           o.update(opt_dict, keys)

           new_options.append(indexed_old_options[option['id']])
           del indexed_old_options[option['id']]
        else:
           new_options.append(models.FieldOption(opt_dict))

        n += 1

    # remove all the not reused old options
    for opt_id in indexed_old_options:
        o = store.find(models.FieldOption, models.FieldOption.id == opt_id).one()
        store.remove(o)

    for o in indexed_old_options:
        store.remove(indexed_old_options[o.id])

    for n in new_options:
        store.add(n)

def field_integrity_check(request):
    is_template = request['is_template']
    step_id = request.get('step_id')
    fieldgroup_id = request.get('fieldgroup_id')

    if is_template == False and \
       (step_id == '' or step_id == None) and \
       (fieldgroup_id == '' or fieldgroup_id == None):
        raise errors.InvalidInputFormat("Each field should be a template or be associated to a step/fieldgroup")

    if not is_template:
        if (step_id == '' or step_id == None) and \
            (fieldgroup_id == '' or fieldgroup_id == None):
            raise errors.InvalidInputFormat("Cannot associate a field to both a step and a fieldgroup")

    return is_template, step_id, fieldgroup_id

def db_create_field(store, request, language):
    """
    Add a new field to the store, then return the new serialized object.
    :param: store: the store reference
    :param: request: the field definition dict
    :param: language: the language of the field definition dict
    :return: a serialization of the object
    """
    is_template, step_id, fieldgroup_id = field_integrity_check(request)

    # XXX you probably want to split this if else statement into two functions
    # that are called create_field_from_template and create_field
    if not 'template_id' in request:
        fill_localized_keys(request, models.Field.localized_strings, language)
        field = models.Field.new(store, request)
        db_update_options(store, field.id, request['options'], language)
    else:
        template = store.find(models.Field, models.Field.id == request['template_id']).one()
        if not template:
            raise errors.InvalidInputFormat("The specified template id %s does not exist" %
                                            request.get('template_id'))
        field = template.copy(store, is_template)

    associate_field(store, field, step_id, fieldgroup_id)

    return anon_serialize_field(store, field, language)

@transact
def create_field(store, request, language):
    return db_create_field(store, request, language)

@transact
def update_field(store, field_id, request, language):
    """
    Updates the specified field with the details.
    raises :class:`globaleaks.errors.FieldIdNotFound` if the field does
    not exist.
    :param: store: the store reference
    :param: field_id: the field_id of the field to update
    :param: request: the field definition dict
    :param: language: the language of the field definition dict
    :return: a serialization of the object
    """
    errmsg = 'Invalid or not existent field ids in request.'

    is_template, step_id, fieldgroup_id = field_integrity_check(request)

    field = models.Field.get(store, field_id)
    try:
        if not field:
            raise errors.InvalidInputFormat(errmsg)

        fill_localized_keys(request, models.Field.localized_strings, language)

        field.update(request)

        # children handling:
        #  - old children are cleared
        #  - new provided childrens are evaluated and added
        children = request['children']
        if children and field.type != 'fieldgroup':
            raise errors.InvalidInputFormat("children can be associated only to fields of type fieldgroup")

        ancestors = set(fieldtree_ancestors(store, field.id))

        field.children.clear()
        for c in children:
            child = models.Field.get(store, c['id'])
            # check child do exists and graph is not recursive
            if not child or child.id == field.id or child.id in ancestors:
                raise errors.InvalidInputFormat(errmsg)

            # remove current step/field fieldgroup/field association
            disassociate_field(store, child.id)

            field.children.add(child)

        db_update_options(store, field.id, request['options'], language)

        # remove current step/field fieldgroup/field association
        disassociate_field(store, field_id)

        associate_field(store, field, step_id, fieldgroup_id)

    except Exception as dberror:
        log.err('Unable to update field: {e}'.format(e=dberror))
        raise errors.InvalidInputFormat(dberror)

    return anon_serialize_field(store, field, language)

@transact_ro
def get_field(store, field_id, is_template, language):
    """
    Serialize a speficied field, localizing its content depending on the language.

    :param field_id: the id corresponding to the field.
    :param language: the language in which to localize data
    :return: the currently configured field.
    :rtype: dict
    """
    field = store.find(models.Field, And(models.Field.id == field_id, models.Field.is_template == is_template)).one()
    if not field:
        log.err('Invalid field requested')
        raise errors.FieldIdNotFound
    return anon_serialize_field(store, field, language)

@transact
def delete_field(store, field_id, is_template):
    """
    Remove the field object corresponding to field_id from the store.

    If the field has children, remove them as well.
    If the field is immediately attached to a step object, remove it as well.

    :param field_id: the id corresponding to the field.
    :raise: FieldIdNotFound: if no such field is found.
    """
    field = store.find(models.Field, And(models.Field.id == field_id, models.Field.is_template == is_template)).one()
    if not field:
        raise errors.FieldIdNotFound
    field.delete(store)

@transact
def get_context_fieldtree(store, context_id):
    """
    Return the serialized field tree belonging to a specific context.

    :param context_id: the id corresponding to the context.
    :return dict: a nested dictionary represending the tree.
    """
    #  context = Context.get(store, context_id)
    steps = store.find(models.Step, models.Step.context_id == context_id).order_by(models.Step.number)
    ret = []
    for step in steps:
        field = models.FieldGroup.get(store, step.field_id)
        ret.append(models.FieldGroup.serialize(store, field.id))
    return ret

def fieldtree_ancestors(store, field_id):
    """
    Given a field_id, recursively extract its parents.

    :param store: appendix to access to the database.
    :param field_id: the parent id.
    :return: a generator of Field.id
    """
    parents = store.find(models.FieldField, models.FieldField.child_id == field_id)
    for parent in parents:
        if parent.parent_id != field_id:
            yield parent.parent_id
            for grandpa in fieldtree_ancestors(store, parent.parent_id): yield grandpa
    else:
        return

@transact_ro
def get_field_list(store, is_template, language):
    """
    Serialize all the root fields (templates or not templates)
    localizing their content depending on the language.

    :return: the current field list serialized.
    :param language: the language of the field definition dict
    :rtype: list of dict
    """
    ret = []

    for f in store.find(models.Field, models.Field.is_template == is_template):
        if not store.find(models.FieldField, models.FieldField.child_id == f.id).one():
            ret.append(anon_serialize_field(store, f, language))

    return ret

class FieldTemplatesCollection(BaseHandler):
    """
    /admin/fieldtemplates
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Return a list of all the fields templates available.

        Parameters: None
        Response: FieldList
        Errors: None
        """
        response = yield get_field_list(True, self.request.language)
        self.set_status(200)
        self.finish(response)

class FieldTemplateCreate(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Create a new field template.

        Request: FieldDesc
        Response: FieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """

        request = self.validate_message(self.request.body,
                                        requests.FieldDesc)

        # enforce difference between /admin/field and /admin/fieldtemplate
        request['is_template'] = True

        response = yield create_field(request, self.request.language)

        self.set_status(201)
        self.finish(response)

class FieldTemplateUpdate(BaseHandler):
    """
    Operation to iterate over a specific requested Field template

    /admin/fieldtemplate/field_id
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, field_id, *uriargs):
        """
        Get the field identified by field_id

        :param field_id:
        :rtype: FieldDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_field(field_id, True, self.request.language)
        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, field_id, *uriargs):
        """
        Update a single field template's attributes.

        Request: FieldDesc
        Response: FieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.FieldDesc)

        # enforce difference between /admin/field and /admin/fieldtemplate
        request['is_template'] = True

        response = yield update_field(field_id, request, self.request.language)
        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, field_id, *uriargs):
        """
        Delete a single field template.

        Request: None
        Response: None
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        yield delete_field(field_id, True)
        self.set_status(200)

class FieldsCollection(BaseHandler):
    """
    /admin/fields
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Return a list of all the fields available in a node.

        Parameters: None
        Response: adminFieldList
        Errors: None
        """
        response = yield get_field_list(False, self.request.language)
        self.set_status(200)
        self.finish(response)

class FieldCreate(BaseHandler):
    """
    Operation to create a field

    /admin/field
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Create a new field.

        Request: FieldDesc
        Response: FieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        tmp = json.loads(self.request.body)
        if 'template_id' in tmp and tmp['template_id'] != '':
            request = self.validate_message(self.request.body,
                                            requests.FieldDescFromTemplate)
        else:
            request = self.validate_message(self.request.body,
                                            requests.FieldDesc)

        # enforce difference between /admin/field and /admin/fieldtemplate
        request['is_template'] = False
        response = yield create_field(request, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')
        GLApiCache.set('contexts', self.request.language, public_contexts_list)

        self.set_status(201)
        self.finish(response)

class FieldUpdate(BaseHandler):
    """
    Operation to iterate over a specific requested Field

    /admin/field
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, field_id, *uriargs):
        """
        Get the field identified by field_id

        :param field_id:
        :rtype: FieldDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_field(field_id, False, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')
        GLApiCache.set('contexts', self.request.language, public_contexts_list)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, field_id, *uriargs):
        """
        Update a single field's attributes.

        Request: FieldDesc
        Response: FieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.FieldDesc)

        # enforce difference between /admin/field and /admin/fieldtemplate
        request['is_template'] = False

        response = yield update_field(field_id, request, self.request.language)

        # get the updated list of contexts, and update the cache
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.invalidate('contexts')
        GLApiCache.set('contexts', self.request.language, public_contexts_list)

        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, field_id, *uriargs):
        """
        Delete a single field.

        Request: None
        Response: None
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        yield delete_field(field_id, False)
        self.set_status(200)
