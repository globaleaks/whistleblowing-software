# -*- coding: UTF-8
#
#   wizard
#   ******
#
# This interface is used to fill the Node defaults whenever they are updated

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.admin import create_context, create_receiver, update_node
from globaleaks.rest import errors, requests
from globaleaks.models import ApplicationData
from globaleaks.utils.utility import log


@transact_ro
def admin_serialize_fields(store, language=GLSetting.memory_copy.default_language):

    appdata = store.find(ApplicationData).one()

    # this condition happen only in the UnitTest
    if not appdata:
        print "no appdata!:w"
        version = 0
        fields = []
    else:
        version = appdata.fields_version
        fields = appdata.fields

    return {
        'version': version,
        'fields': list(fields)
    }

@transact
def update_application_fields(store, version, appfields):

    appdata = store.find(ApplicationData).one()

    if not appdata:
        appdata = ApplicationData()
        has_been_updated = True
        old_version = 0
        store.add(appdata)
    elif appdata.fields_version > version:
        has_been_updated = False
        old_version = appdata.fields_version
    else: # appdata not None and new_v >= old_v
        has_been_updated = True
        old_version = appdata.fields_version

    if has_been_updated:

        log.debug("Updating Application Data Fields %d => %d" %
                  (old_version, version))

        appdata.fields = appfields
        appdata.fields_version = version
    else:
        log.err("NOT updating the Application Data Fields current %d proposed %d" %
                (appdata.fields_version, version))

    # in both cases, update or not, return the running version
    return {
        'version': appdata.fields_version,
        'fields': appdata.fields,
    }



# ---------------------------------
# Below starts the Cyclone handlers
# ---------------------------------

class FieldsCollection(BaseHandler):
    """
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    /admin/wizard/fields
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):

        self.set_status(200)

        app_fields_dump = yield admin_serialize_fields(self.request.language)
        self.finish(app_fields_dump)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):

        accepted_types = [ "text", "radio", "select", "checkboxes",
            "textarea", "number", "url", "phone", "email" ]

        request = self.validate_message(self.request.body,
                requests.wizardFieldUpdate)

        fields = request['fields']
        log.debug("Received update of Application Data Fields (%d elements)" % len(fields))

        for field in fields:
            if field['type'] not in accepted_types:
                log.debug("Invalid type received: %s" % field['type'])
                raise errors.InvalidInputFormat("Invalid type supply")

        app_fields_dump = yield update_application_fields(request['version'], fields)

        self.set_status(202) # Updated
        self.finish(app_fields_dump)



class FirstSetup(BaseHandler):
    """
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):

        self.set_status(200)

        request = self.validate_message(self.request.body,
                requests.wizardFirstSetup)

        log.debug("Wizard initialization setup!")

        receiver = request['receiver']
        context = request['context']
        node = request['node']
        fields = request['fields']

        try:
            accepted_types = [ "text", "radio", "select", "checkboxes",
                               "textarea", "number", "url", "phone", "email" ]
            for field in fields:
                if field['type'] not in accepted_types:
                    log.debug("Invalid type received: %s" % field['type'])
                    raise errors.InvalidInputFormat("Invalid type supply")

            yield update_application_fields(request['version'], fields)

        except Exception as excep:
            log.debug("Failed Fields initialization %s" % excep)
            raise excep

        try:
            context_dict = yield create_context(context, self.request.language)
        except Exception as excep:
            log.debug("Failed Context initialization %s" % excep)
            raise excep

        try:
            receiver['context']= [ context_dict['id'] ]
            yield create_receiver(receiver, self.request.language)
        except Exception as excep:
            log.debug("Failed Receiver Finitialization %s" % excep)
            raise excep

        try:
            yield update_node(node, wizard_done=True, request=self.request.language)
        except Exception as excep:
            log.debug("Failed Fields initialization %s" % excep)
            raise excep

        self.set_status(202) # Updated
        self.finish()


