# -*- coding: UTF-8
#
#   wizard
#   ******
#
# This interface is used to fill the Node defaults whenever they are updated

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler, GLApiCache
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.admin import db_create_context, db_create_receiver, db_update_node, \
                                      anon_serialize_node, get_public_context_list, get_public_receiver_list

from globaleaks.rest import errors, requests
from globaleaks.models import *
from globaleaks.utils.utility import log

from twisted.internet.defer import inlineCallbacks


@transact_ro
def admin_serialize_appdata(store, language=GLSetting.memory_copy.default_language):

    appdata = store.find(ApplicationData).one()

    # this condition happens only in the UnitTest
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

        for key in  ['presentation', 'footer', 'subtitle',
                     'security_awareness_title', 'security_awareness_text',
                     'whistleblowing_question', 'whistleblowing_button']:

            if key in loaded_appdata['node']:
                setattr(node, key, loaded_appdata['node'][key])

    else:
        log.err("NOT updating the Application Data Fields current %d proposed %d" %
                (appdata.version, loaded_appdata['version']))

    # in both cases, update or not, return the running version
    return {
        'version': appdata.version,
        'fields': appdata.fields,
    }

@transact
def wizard(store, request, language=GLSetting.memory_copy.default_language):

    node = request['node']
    context = request['context']
    receiver = request['receiver']

    node['default_language'] = language
    node['languages_enabled'] = [ language ]

    try:
        db_update_node(store, node, True, language)

    except Exception as excep:
        log.err("Failed Node initialization %s" % excep)
        raise excep

    try:
        context_dict = db_create_context(store, context, language)
    except Exception as excep:
        log.err("Failed Context initialization %s" % excep)
        raise excep

    # associate the new context to the receiver
    receiver['contexts'] = [ context_dict['id'] ]

    try:
        db_create_receiver(store, receiver, language)
    except Exception as excep:
        log.err("Failed Receiver Initialization %s" % excep)
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
                requests.wizardAppdataDesc)

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

        # cache must be updated in particular to set wizard_done = True
        public_node_desc = yield anon_serialize_node(self.request.language)
        GLApiCache.invalidate('node')
        GLApiCache.invalidate('contexts')
        GLApiCache.invalidate('receivers')
        GLApiCache.set('node', self.request.language, public_node_desc)
        public_contexts_list = yield get_public_context_list(self.request.language)
        GLApiCache.set('contexts', self.request.language, public_contexts_list)
        public_receivers_list = yield get_public_receiver_list(self.request.language)
        GLApiCache.set('receivers', self.request.language, public_receivers_list)

        self.set_status(201) # Created
        self.finish()

