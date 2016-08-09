# -*- coding: UTF-8
#
# wizard

from globaleaks import models, security
from globaleaks.orm import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin.context import db_create_context
from globaleaks.handlers.admin.receiver import db_create_receiver
from globaleaks.handlers.admin.user import db_create_admin_user
from globaleaks.handlers.public import serialize_node
from globaleaks.models.l10n import EnabledLanguage
from globaleaks.models import ConfigL10N as c_l10n
from globaleaks.models.config import NodeFactory
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_null

from twisted.internet.defer import inlineCallbacks


@transact
def wizard(store, request, language):
    node = NodeFactory(store)

    if node.get_val('wizard_done'):
        # TODO report as anomaly
        log.err("DANGER: Wizard already initialized!")
        raise errors.ForbiddenOperation
    try:
        node._query_group()

        nn = unicode(request['node']['name'])
        node.set_val('name', nn)
        node.set_val('default_language', language)
        node.set_val('allow_unencrypted', request['node']['allow_unencrypted'])
        node.set_val('wizard_done', True)

        c_l10n.get_one(store, language, 'node', 'description').value = nn
        c_l10n.get_one(store, language, 'node', 'header_title_homepage').value = nn
        c_l10n.get_one(store, language, 'node', 'presentation').value = nn

        context = db_create_context(store, request['context'], language)

        langs_to_drop = EnabledLanguage.get_all_strs(store)
        langs_to_drop.remove(language)
        for lang_code in langs_to_drop:
            EnabledLanguage.remove_old_lang(store, lang_code)

        request['receiver']['contexts'] = [context.id]
        request['receiver']['language'] = language
        db_create_receiver(store, request['receiver'], language)

        admin_dict = {
            'username': u'admin',
            'password': request['admin']['password'],
            'role': u'admin',
            'state': u'enabled',
            'deletable': False,
            'name': u'Admin',
            'public_name': u'Admin',
            'description': u'',
            'mail_address': request['admin']['mail_address'],
            'language': language,
            'timezone': node.get_val('default_timezone'),
            'password_change_needed': False,
            'pgp_key_remove': False,
            'pgp_key_status': 'disabled',
            'pgp_key_info': '',
            'pgp_key_fingerprint': '',
            'pgp_key_public': '',
            'pgp_key_expiration': datetime_null()
        }

        db_create_admin_user(store, admin_dict, language)

    except Exception as excep:
        log.err("Failed wizard initialization %s" % excep)
        raise excep


class Wizard(BaseHandler):
    """
    Setup Wizard handler
    """
    @BaseHandler.unauthenticated
    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.body,
                                        requests.WizardDesc)

        # Wizard will raise exceptions if there are any errors with the request
        yield wizard(request, self.request.language)
        # cache must be updated in order to set wizard_done = True
        yield serialize_node(self.request.language)
        GLApiCache.invalidate()

        self.set_status(201)  # Created
