# -*- coding: UTF-8
#
# wizard
from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.admin.context import db_create_context
from globaleaks.handlers.admin.user import db_create_admin_user, db_create_receiver_user
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import config, l10n, profiles
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_null


@transact
def wizard(store, request, language):
    models.db_delete(store, l10n.EnabledLanguage, l10n.EnabledLanguage.name != language)

    node = config.NodeFactory(store)

    if node.get_val('wizard_done'):
        log.err("DANGER: Wizard already initialized!")
        raise errors.ForbiddenOperation

    node._query_group()

    node.set_val('name', request['node']['name'])
    node.set_val('default_language', language)
    node.set_val('wizard_done', True)

    if GLSettings.memory_copy.onionservice is not None:
        node.set_val('onionservice', GLSettings.memory_copy.onionservice)

    node_l10n = l10n.NodeL10NFactory(store)

    node_l10n.set_val('description', language, request['node']['description'])
    node_l10n.set_val('header_title_homepage', language, request['node']['name'])

    profiles.load_profile(store, request['profile'])

    context = db_create_context(store, request['context'], language)

    request['receiver']['contexts'] = [context.id]
    request['receiver']['language'] = language
    db_create_receiver_user(store, request['receiver'], language)

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
        'password_change_needed': False,
        'pgp_key_remove': False,
        'pgp_key_fingerprint': '',
        'pgp_key_public': '',
        'pgp_key_expiration': datetime_null()
    }

    db_create_admin_user(store, admin_dict, language)

    db_refresh_memory_variables(store)


class Wizard(BaseHandler):
    """
    Setup Wizard handler
    """
    check_roles = 'unauthenticated'
    invalidate_cache = True

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.WizardDesc)

        return wizard(request, self.request.language)
