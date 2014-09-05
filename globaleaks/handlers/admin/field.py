# -*- coding: UTF-8
#
#   fields
#   ******
#
# Implementation of the code executed when an HTTP client reach /admin/fields URI
#
import os
import shutil

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import errors, requests
from globaleaks.models import ApplicationData, Field, FieldGroup, FieldGroupFieldGroup, Step
from globaleaks.utils.utility import log, datetime_now, datetime_null, datetime_to_ISO8601


def serialize_field_group(store, field_group):
    """
    Function that perform serialization of a field given the id
    whenever the fieldgroup is directly associated with a Field the serialization include Field informations.
    :param store: the store object to be used
    :param field_group: the field_group object to be serialized
    :return: a serialization of the object
    """

    ret =  {
        'id': field_group.id,
        'label': field_group.label,
        'description': field_group.description,
        'hint': field_group.hint,
        'multi_entry': field_group.multi_entry,
        'x': field_group.x,
        'y': field_group.y,
    }

    field = store.find(Field, Field.id == field_group.id).one()

    if field:
        ret.update({
            'type': field.type,
            'stats_enabled': field.stats_enabled,
            'required': field.required,
            'options': field.options,
            'preview': False
        })
    else:
        ret.update({
            'childrens': [f.id for f in field_group.children]
        })

    return ret

@transact_ro
def transact_serialize_field_group(store, field_group_id):
    """
    Transaction that perform serialization of a FieldGroup_ given the id
    whenever the fieldgroup is directly associated with a Field the serialization include Field informations.
    :param store: the store object provided by the transact decorator
    :param field_id: the field_id of the object to be serialized
    :return: a serialization of the object identified by field_id
    """

    field_group = store.find(FieldGroup, FieldGroup.id == unicode(field_group_id)).one()

    return serialize_field_group(store, field_group)

# HACK
def convert_answer_to_request(answer_field):
    """
    @param answer_field: something defined in
        globaleaks.tests.TI_testdata
    @return: a dict localized in a specific language only (e.g., in 'it')
    """
    return  {
        'label' : u'Sei un dipendente pubblico o privato ?',
        'description' :u"Descrizione - Cosa devo mettere qui ?",
        'hint' : u'Se sei un dipendente pubblico non sarai mai licenziato: complimenti! ಠ_ಠ ',
        'multi_entry' : True,
        'x' : 1,
        'y' : 1,
        'type' : 'selectbox',
        'stats_enabled' : True,
        'required' : True,
        'options': {
                'RANDOMKEY' : {
                        'label': u'Dipendente pubblico',
                        'trigger': u'00000000-0000-0000-0000-0000PUBBLICO',
                        },
                'OTHERRANDOM' : {
                        'label': u'Dipendente privato',
                        'trigger': u'00000000-0000-0000-0000-00000PRIVATO',
                    }
            },
        'default_value' : True,
        'preview' : False,
    }


@transact
def update_field(store, field_id, request, language=GLSetting.memory_copy.default_language):
    pass


@transact
def create_field(store, request, language=GLSetting.memory_copy.default_language):
    request = convert_answer_to_request(None)

    pass


@transact_ro
def transact_get_field_list(store, language=GLSetting.memory_copy.default_language):
    """
    Returns:
        (dict) the current field list serialized.
    """

    # TODO clarify the madness: Field, FieldGroup, Step, FieldGroupFieldGroup
    A = store.find(Field)
    B = store.find(FieldGroup)
    C = store.find(FieldGroupFieldGroup)
    D = store.find(Step)

    field_list = []

    for f in B:
        serialized_field = serialize_field_group(store, f)
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
def delete_field(field_id):
    raise Exception("Not implemented ATM %s" % str(field_id))


@transact
def get_context_fieldtree(store, context_id):
    """
    Return the serialized field_group tree belonging to a specific context.

    :return dict: a nested disctionary represending the tree.
    """
    #  context = Context.get(store, context_id)
    steps = store.find(Step, Step.context_id == context_id).order_by(Step.number)
    ret = []
    for step in steps:
        field = FieldGroup.get(store, step.field_group_id)
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
        Errors: InvalidInputFormat, FieldNotFound
        """
        request = self.validate_message(self.request.body, requests.adminFieldDesc)
        response = yield create_field(request, self.request.language)

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
        Errors: FieldNotFound, InvalidInputFormat
        """
        response = yield get_field(field_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, field_id, *uriargs):
        """
        Request: adminFieldDesc
        Response: adminFieldDesc
        Errors: InvalidInputFormat, FieldNotFound
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
        Request: None
        Response: None
        Errors: InvalidInputFormat, FieldNotFound
        """
        yield delete_field(field_id)
        self.set_status(200)
