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

def serialize_field(field, field_group):
    """
    This function is called only inside a @transact[_ro]

    @param field: Storm object
    @param field_group: Storm object
    @return: TODO stabilize field format for GLClient

    AT THE MOMENT WE'RE RETURNING A STATIC FIELD IN CLIENT VERSION
    """
    from globaleaks.tests.TI_testdata import TI_1
    return TI_1


# HACK
def convert_answer_to_request(answer_field):
    """
    @param answer_field: something defined in
        globaleaks.tests.TI_testdata
    @return: something WITH ONLY ONE LANGUAGE ('it'
    """
    return  {
        'label' : u'Sei un dipendente pubblico o privato ?',
        'description' :u"Descrizione - Cosa devo mettere qui ?",
        'hint' : u'Se sei un dipendente pubblico non sarai mai licenziato: complimenti! ಠ_ಠ ',
        'multi_entry' : True,
        'x' : 1,
        'y' : 1,
        'type' : 'checkbox',
        'stats_enabled' : True,
        'required' : True,
        'regexp' : '.*', # this is fine, or just saying 'None' is good ? TODO check
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
def get_field_list(store, language=GLSetting.memory_copy.default_language):
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

    return field_list


@transact_ro
def get_field(store, field_id, language=GLSetting.memory_copy.default_language):
    """
    Returns:
        (dict) the currently configured node.
    """
    context = store.find(Field, Field.id == unicode(field_id)).one()

    if not context:
        log.err("Requested invalid context")
        raise errors.ContextIdNotFound

    from globaleaks.tests.TI_testdata import TI_1
    # maker has already implemented serialization - but is not commited H.F.S.!
    return TI_1

@transact
def delete_field(field_id):
    raise Exception("Not implemented ATM %s" % str(field_id))


class FieldsCollection(BaseHandler):
    """

    /admin/context
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
        response = yield get_field_list(self.request.language)

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

