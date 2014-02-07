# -*- coding: UTF-8
#
#   wizard
#   ******
#
# This interface is used to fill the Node defaults whenever they are updated


from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check, unauthenticated
from globaleaks.rest import errors, requests
from globaleaks.models import Context, Node, User
from globaleaks import security, models
from globaleaks.utils import utility, structures
from globaleaks.utils.utility import log
from globaleaks.db.datainit import import_memory_variables
from globaleaks import LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED


temporary_fields_dump = []

# how to use this temporary status
#
#   pip install httpie
#
# GLBackend$ http 127.0.0.1:8082/admin/wizard `cat test_fields.json`

def wizard_serialize_fields(fields, language=GLSetting.memory_copy.default_language):
    """
    @param fields:
    @return:
        Need to be investigated (wizard use full languages and not a single one)
    """

    return temporary_fields_dump


# ---------------------------------
# Below starts the Cyclone handlers
# ---------------------------------

class FieldsCollection(BaseHandler):
    """
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    /admin/wizard/fields
    """
    # @transport_security_check('admin')
    # @authenticated('admin')
    @unauthenticated
    @inlineCallbacks
    def get(self, *uriargs):

        self.set_status(200)
        self.finish(temporary_fields_dump)

    # @transport_security_check('admin')
    # @authenticated('admin')
    @unauthenticated
    # @inlineCallbacks
    def post(self, *uriargs):
        """
        only accepted types:
          "type":"text"
          "type":"radio",
          "type":"select",
          "type":"checkboxes",
          "type":"textarea"
          "type":"number"
          "type":"url"
          "type":"phone"
          "type":"email"
        """

        request = self.validate_message(self.request.body,
                requests.wizardFieldUpdate)

        fields = request['fields']
        log.debug("Updating Application Data (Fields) to version: %d" % request['version'])

        temporary_fields_dump = list(fields)

        self.set_status(202) # Updated
        self.finish(temporary_fields_dump)



