# -*- coding: UTF-8
#
# wizard
# ******
#
# This interface is used to fill the Node defaults whenever they are updated

from globaleaks.handlers.base import BaseHandler, GLApiCache
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.admin import db_create_context, db_create_receiver, \
        db_update_node
from globaleaks.handlers.node import anon_serialize_node, \
        get_public_context_list, get_public_receiver_list
from globaleaks.rest import requests
from globaleaks.settings import transact
from globaleaks.utils.utility import log

from twisted.internet.defer import inlineCallbacks


@transact
def wizard(store, request, language):
    node = request['node']
    context = request['context']
    receiver = request['receiver']

    node['default_language'] = language
    node['languages_enabled'] = [language]

    # Header title of the homepage is initially set with the node title
    node['header_title_homepage'] = node['name']

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
    receiver['contexts'] = [context_dict['id']]

    try:
        db_create_receiver(store, receiver, language)
    except Exception as excep:
        log.err("Failed Receiver Initialization %s" % excep)
        raise excep


# ---------------------------------
# Below starts the Cyclone handlers
# ---------------------------------

class FirstSetup(BaseHandler):
    """
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        """

        request = self.validate_message(self.request.body,
                                        requests.WizardFirstSetupDesc)

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

        self.set_status(201)  # Created
        self.finish()

