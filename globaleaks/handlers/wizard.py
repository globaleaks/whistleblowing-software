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
from globaleaks.handlers.admin import db_create_context, db_create_receiver, db_update_node
from globaleaks.rest import errors, requests
from globaleaks.models import *
from globaleaks.utils.utility import log


@transact_ro
def admin_serialize_appdata(store, language=GLSetting.memory_copy.default_language):

    appdata = store.find(ApplicationData).one()

    # this condition happen only in the UnitTest
    if not appdata:
        version = 0
        fields = []
    else:
        version = appdata.version
        fields = appdata.fields

    return {
        'version': version,
        'fields': list(fields)
    }

@transact
def admin_update_appdata(store, loaded_appdata):

    appdata = store.find(ApplicationData).one()
    node = store.find(Node).one()

    if not appdata:
        appdata = ApplicationData()
        has_been_updated = True
        old_version = 0
        store.add(appdata)
    elif appdata.version > loaded_appdata['version']:
        has_been_updated = False
        old_version = appdata.version
    else: # appdata not None and new_v >= old_v
        has_been_updated = True
        old_version = appdata.version

    if has_been_updated:

        log.debug("Updating Application Data Fields %d => %d" %
                  (old_version, loaded_appdata['version']))

        appdata.version = loaded_appdata['version']

        try:

            log.debug("Validating %d fields" % len(loaded_appdata['fields']))

            accepted_types = [ "text", "radio", "select", "checkboxes",
                               "textarea", "number", "url", "phone", "email" ]

            for field in loaded_appdata['fields']:
                if field['type'] not in accepted_types:
                    log.debug("Invalid type received: %s" % field['type'])
                    raise errors.InvalidInputFormat("Invalid type supply")

            appdata.fields = loaded_appdata['fields']

        except Exception as excep:
            log.debug("Failed Fields initialization %s" % excep)
            raise excep

        if 'node_presentation' in loaded_appdata:
            node.presentation = loaded_appdata['node_presentation']

        if 'node_footer' in loaded_appdata:
            node.footer = loaded_appdata['node_footer']

        if 'node_subtitle' in loaded_appdata:
            node.subtitle = loaded_appdata['node_subtitle']

    else:
        log.err("NOT updating the Application Data Fields current %d proposed %d" %
                (appdata.version, version))

    # in both cases, update or not, return the running version
    return {
        'version': appdata.version,
        'fields': appdata.fields,
    }

@transact
def wizard(store, request, language=GLSetting.memory_copy.default_language):

    receiver = request['receiver']
    context = request['context']
    node = request['node']

    node['default_language'] = language
    node['languages_enabled'] = [ language ]

    try:
        context_dict = db_create_context(store, context, language)
    except Exception as excep:
        log.err("Failed Context initialization %s" % excep)
        raise excep

    # associate the new context to the receiver 
    receiver['contexts'] = [ context_dict['id'] ]

    try:
        receiver_dict = db_create_receiver(store, receiver, language)
    except Exception as excep:
        log.err("Failed Receiver Finitialization %s" % excep)
        raise excep

    try:
        db_update_node(store, node, True, language)
    except Exception as excep:
        log.err("Failed Node initialization %s" % excep)
        raise excep

# ---------------------------------
# Below starts the Cyclone handlers
# ---------------------------------

class AppdataCollection(BaseHandler):
    """
    Get the node main settings, update the node main settings, it works in a single static
    table, in models/admin.py

    /admin/wizard/fields
    """
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):

        app_fields_dump = yield admin_serialize_appdata(self.request.language)

        self.set_status(200)
        self.finish(app_fields_dump)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):

        request = self.validate_message(self.request.body,
                requests.wizardFieldUpdate)

        app_fields_dump = yield admin_update_appdata(request)

        self.set_status(202) # Updated
        self.finish(app_fields_dump)


class FirstSetup(BaseHandler):
    """
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        """

        request = self.validate_message(self.request.body,
                requests.wizardFirstSetup)

        yield wizard(request, self.request.language)

        self.set_status(201) # Created
        self.finish()

