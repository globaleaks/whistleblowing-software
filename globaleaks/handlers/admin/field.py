# -*- coding: UTF-8
#
#   fields
#   ******
#
# Implementation of the code executed when an HTTP client reach /admin/fields URI
#
import os
import shutil

from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import errors, requests
from globaleaks.models import ApplicationData, Field, Step
from globaleaks.utils.utility import log, datetime_now, datetime_null, datetime_to_ISO8601


def admin_serialize_field(store, field, language):
    """
    Function that perform serialization of a field given the id
    whenever the fieldgroup is directly associated with a Field the serialization include Field informations.
    :param store: the store object to be used
    :param field: the field object to be serialized
    :return: a serialization of the object
    """
    ret =  {
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
        'options': field.options
    }

    if field.children:
        ret.update({
            'children': [f.id for f in field.children]
        })

    return ret

@transact_ro
def transact_admin_serialize_field(store, field_id):
    """
    Transaction that perform serialization of a FieldGroup_ given the id
    whenever the fieldgroup is directly associated with a Field the serialization include Field informations.
    :param store: the store object provided by the transact decorator
    :param field_id: the field_id of the object to be serialized
    :return: a serialization of the object identified by field_id
    """

    field = store.find(FieldGroup, FieldGroup.id == unicode(field_id)).one()

    return admin_serialize_field(store, field)

def db_create_field(store, request, language=GLSetting.memory_copy.default_language):
    field = Field.new(store, request)

    return field

@transact
def transact_create_field(store, request, language=GLSetting.memory_copy.default_language):
    field = db_create_field(store, request, language=language)

    return admin_serialize_field(store, field, language)


def db_update_field(store, field_id, request, language=GLSetting.memory_copy.default_language):
    field = Field.get(store, field_id)

    try:
        field.update(request)
    except Exception as dberror:
        log.err("Unable to update receiver %s: %s" % (receiver.name, dberror))
        raise errors.InvalidInputFormat(dberror)

    return field

@transact
def transact_update_field(store, field_id, request, language=GLSetting.memory_copy.default_language):
    """
    Updates the specified receiver with the details.
    raises :class:`globaleaks.errors.ReceiverIdNotFound` if the receiver does
    not exist.
    """
    field = db_update_field(store, field_id, request, language=GLSetting.memory_copy.default_language)

    return admin_serialize_field(store, field, language)


@transact_ro
def transact_get_field_list(store, language=GLSetting.memory_copy.default_language):
    """
    Returns:
        (dict) the current field list serialized.
    """

    # TODO clarify the madness: Field, FieldGroup, Step, FieldGroupFieldGroup
    A = store.find(Field)
    B = store.find(Step)

    field_list = []

    for f in A:
        serialized_field = admin_serialize_field(store, f, language)
        field_list.append(serialized_field)

    return field_list


@transact_ro
def get_field(store, field_id, language=GLSetting.memory_copy.default_language):
    """
    Returns:
        (dict) the currently configured field.
    """
    field = store.find(Field, Field.id == unicode(field_id)).one()

    if not field:
        log.err("Requested invalid field")
        raise errors.FieldIdNotFound

    return {}

@transact
def transact_delete_field(store, field_id):
    field = store.find(Field, Field.id == unicode(field_id)).one()

    if not field:
        log.err("Requested invalid field")
        raise errors.FieldIdNotFound

    store.remove(field)


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


class FieldsCollection(BaseHandler):
    """

    /admin/fields
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminFieldList
        Errors: None
        """
        # XXX TODO REMIND: is pointless define Response format because we're not making output validation
        response = yield transact_get_field_list(self.request.language)

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
        request = self.validate_message(self.request.body, requests.adminFieldDesc)
        response = yield transact_create_field(request, self.request.language)

        self.set_status(201) # Created
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
        Parameters: field_id
        Response: adminFieldDesc
        Errors: FieldIdNotFound, InvalidInputFormat
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

        response = yield transact_create_field(request, self.request.language)

        self.set_status(201) # Created
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, field_id, *uriargs):
        """
        Request: adminFieldDesc
        Response: adminFieldDesc
        Errors: InvalidInputFormat, FieldIdNotFound
        """

        request = self.validate_message(self.request.body,
                                        requests.adminFieldDesc)

        response = yield transact_update_field(field_id, request, self.request.language)

        self.set_status(202) # Updated
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def delete(self, field_id, *uriargs):
        """
        Request: None
        Response: None
        Errors: InvalidInputFormat, FieldIdNotFound
        """
        yield transact_delete_field(field_id)
        self.set_status(200)