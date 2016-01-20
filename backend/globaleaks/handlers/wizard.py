# -*- coding: UTF-8
#
# wizard

from globaleaks import models, security
from globaleaks.orm import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.admin.context import db_create_context
from globaleaks.handlers.admin.receiver import db_create_receiver
from globaleaks.handlers.admin.node import db_update_node
from globaleaks.handlers.node import serialize_node
from globaleaks.rest import requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.utility import log

from twisted.internet.defer import inlineCallbacks


@transact
def wizard(store, request, language):
    try:
        request['node']['default_language'] = language
        request['node']['languages_enabled'] = [language]

        # Header title of the homepage and the node presentation is
        # initially set with the node title
        request['node']['header_title_homepage'] = request['node']['name']
        request['node']['presentation'] = request['node']['name']

        db_update_node(store, request['node'], True, language)
        context = db_create_context(store, request['context'], language)

        # associate the new context to the receiver
        request['receiver']['contexts'] = [context.id]

        db_create_receiver(store, request['receiver'], language)

        admin = store.find(models.User, (models.User.username == unicode('admin'))).one()

        admin.mail_address = request['admin']['mail_address']

        password = request['admin']['password']
        old_password = request['admin']['old_password']

        if password and old_password and len(password) and len(old_password):
            admin.password = security.change_password(admin.password,
                                                      old_password,
                                                      password,
                                                      admin.salt)
    except Exception as excep:
        log.err("Failed wizard initialization %s" % excep)
        raise excep


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
        public_node_desc = yield serialize_node(self.request.language)
        GLApiCache.invalidate()

        self.set_status(201)  # Created
        self.finish()
