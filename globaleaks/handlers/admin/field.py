# -*- coding: UTF-8
"""
Implementation of the code executed when an HTTP client reach /admin/fields URI.
"""
from __future__ import unicode_literals

from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.models import Field, Step
from globaleaks.rest import errors, requests
from globaleaks.settings import transact, transact_ro
from globaleaks.utils.utility import log

def admin_serialize_field(field, language):
    """
    Serialize a field, localizing its content depending on the language.

    :param field: the field object to be serialized
    :param language: the language in which to localize data
    :return: a serialization of the object
    """
    return {
        'id': field.id,
        'label': field.label,
        'description': field.description,
        'hint': field.hint,
        'multi_entry': field.multi_entry,
        'required': field.required,
        'preview': False,
        'stats_enabled': field.stats_enabled,
        'type': field.type,
        'x': field.x,
        'y': field.y,
        'options': field.options or {},
        'children': [f.id for f in field.children],
    }

@transact
def create_field(store, request, language):
    """
    Add a new field to the store, then return the new serialized object.
    """
    field = Field.new(store, request)
    return admin_serialize_field(field, language)

@transact
def update_field(store, field_id, request, language):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverIdNotFound` if the receiver does
    not exist.
    """
    field = Field.get(store, field_id)
    try:
        field.update(request)
    except Exception as dberror:
        log.err('Unable to update receiver {r}: {e}'.format(
            r=receiver.name, e=dberror))
        raise errors.InvalidInputFormat(dberror)
    return admin_serialize_field(field, language)

@transact_ro
def get_field_list(store, language):
    """
    :return: the current field list serialized.
    :rtype: dict
    """
    return [admin_serialize_field(f, language) for f in store.find(Field)]

@transact_ro
def get_field(store, field_id, language):
    """
    :return: the currently configured field.
    :rtype: dict
    """
    field = Field.get(store, field_id)
    if not field:
        log.err('Invalid field requested')
        raise errors.FieldIdNotFound
    return admin_serialize_field(field, language)

@transact
def delete_field(store, field_id):
    """
    Remove the field object corresponding to field_id from the store.
    If the field has children, remove them as well.
    If the field is immediately attached to a step object, remove it as well.

    :param field_id: the id correstponding to the field.
    :raises FieldIdNotFound: if no such field is found.
    """
    field = Field.get(store, field_id)
    if not field:
        raise errors.FieldIdNotFound
    step = store.find(Step, Step.field == field.id)
    if step.any():
        step = step.one()
        step.delete(store)
    field.delete(store)

@transact
def get_context_fieldtree(store, context_id):
    """
    Return the serialized field tree belonging to a specific context.

    :return dict: a nested disctionary represending the tree.
    """
    #  context = Context.get(store, context_id)
    steps = store.find(Step, Step.context_id == context_id).order_by(Step.number)
    ret = []
    for step in steps:
        field = FieldGroup.get(store, step.field_id)
        ret.append(FieldGroup.serialize(store, field.id))
    return ret

def fieldtree_ancestors(store, field_id):
    """
    Given a field_id, recursively extract its parents.

    :param store: appendix to access to the database.
    :param field_id: the parent id.
    :return: a generator of Field.id
    """
    yield field_id
    parents = store.find(models.FieldField, models.FieldField.child_id == field_id)
    for parent in parents:
        yield parent.id
        # yield from field_ancestors(store, parent_id)
        for grandpa in field_ancestors(store, parent.id): yield grandpa
    else:
        return

@transact
def update_fieldtree(store, tree, language):
    """
    Update field groups to host different fields, making sure that:
    - the tree is non-recursive
    - the tree is consistent with the fields present.

    :return: a serialized summary of the items that have been modified.
    """
    errmsg = 'Invalid or not existent field ids in request.'
    resp = []

    for node in tree:
        field = Field.get(store, node['id'])
        if not field or field.type != 'fieldgroup':
            raise errors.InvalidInputFormat(errmsg)
        children = node['children']
        ancestors = set(fieldtree_ancestors(store, field.id))
        # re-make the list of children with the one receieved.
        field.children.clear()
        for child_id in children:
            child = Field.get(store, child_id)
            # check child do exists and graph is not recursive
            if not child or child in ancestors:
                raise errors.InvalidInputFormat(errmsg)
            field.children.add(child)
            # add (serialized) current item as response
        resp.append(admin_serialize_field(field, language))
    return resp

@transact
def delete_steps(store, steps_desc):
    """
    Remove a collection of steps, given their context_id and number.

    :raises errors.ModelNotFound: if any of the items has not been found on the
                                  database.
    """
    steps = [Step.get(store, step_desc['context_id'], step_desc['number'])
             for step_desc in steps_desc]
    if None in steps:
        raise errors.ModelNotFound(Step)
    for step in steps:
        step.delete(store)

class StepsCollection(BaseHandler):
    """
    /admin/fields/step/
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Create a new step.
        If a precise location is given, put it in the described location and
        shift all the others.
        the others.
        """
        # validate
        # create a new fieldgroup
        # create a new step

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, *uriargs):
        """
        Update the step orders.
        """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, *uriargs):
        """
        Remove a step.
        """
        request = self.validate_message(self.request.body,
                                         requests.adminStepDescList)
        yield delete_steps(request)
        self.set_status(200)
        # XXX. not sure about what we should return in here.


class FieldsCollection(BaseHandler):
    """
    /admin/fields
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Return a list of all the fields available.

        Parameters: None
        Response: adminFieldList
        Errors: None
        """
        # XXX TODO REMIND: is pointless define Response format because we're not
        # making output validation
        response = yield get_field_list(self.request.language)
        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, *uriargs):
        """
        Rearrange a field tree, moving field to the group selected by the user,
        and groups to the correspective steps.

        :raises InvalidInputFormat: if the tree sent presents some inconsistencies.
        """
        request = self.validate_message(self.request.body,
                                        requests.adminFieldTree)
        response = yield update_fieldtree(request, self.request.language)
        self.set_status(201)
        self.finish(response)


class FieldInstance(BaseHandler):
    """
    Operation to iterate over a specific requested Field

    /admin/field/field_id
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, field_id, *uriargs):
        """
        Get the field identified by field_id

        :param field_id:
        :rtype: adminFieldDesc
        :raises FieldIdNotFound: if there is no field with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_field(field_id, self.request.language)
        self.set_status(200)
        self.finish(response)


    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: adminFieldDesc
        Response: adminFieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """

        request = self.validate_message(self.request.body,
                                        requests.adminFieldDesc)

        response = yield create_field(request, self.request.language)

        self.set_status(201) # Created
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Create a new field.

        Request: adminFieldDesc
        Response: adminFieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.adminFieldDesc)
        response = yield create_field(request, self.request.language)
        self.set_status(201)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, field_id, *uriargs):
        """
        Update a single field's attributes.

        Request: adminFieldDesc
        Response: adminFieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.adminFieldDesc)
        response = yield update_field(field_id, request, self.request.language)
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
        yield delete_field(field_id)
        self.set_status(200)
