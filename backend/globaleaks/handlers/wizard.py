# -*- coding: utf-8
#
# Handlers implementing platform wizard
from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.admin.context import db_create_context
from globaleaks.handlers.admin.node import db_update_enabled_languages
from globaleaks.handlers.admin.user import db_create_user, db_create_receiver_user
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import config, profiles
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.utils.utility import log


def db_wizard(session, state, tid, request, create_admin, client_using_tor, language):
    language = request['node_language']

    node = config.ConfigFactory(session, tid, 'node')

    if node.get_val(u'wizard_done'):
        log.err("DANGER: Wizard already initialized!", tid=tid)
        raise errors.ForbiddenOperation

    db_update_enabled_languages(session, tid, [language], language)

    if tid != 1:
        tenant = models.db_get(session, models.Tenant, models.Tenant.id == tid)
        tenant.label = request['node_name']

    node.set_val(u'name', request['node_name'])
    node.set_val(u'default_language', language)
    node.set_val(u'wizard_done', True)
    node.set_val(u'enable_developers_exception_notification', request['enable_developers_exception_notification'])

    # Guess Tor configuration from thee media used on first configuration and
    # if the user is using Tor preserve node anonymity and perform outgoing connections via Tor
    node.set_val(u'reachable_via_web', not client_using_tor)
    node.set_val(u'allow_unencrypted', not client_using_tor)
    node.set_val(u'anonymize_outgoing_connections', client_using_tor)
    node.set_val(u'disable_encryption_warnings', not client_using_tor)

    node_l10n = config.NodeL10NFactory(session, tid)
    node_l10n.set_val(u'header_title_homepage', language, request['node_name'])

    profiles.load_profile(session, tid, request['profile'])

    if create_admin:
        admin_desc = models.User().dict(language)
        admin_desc['name'] = request['admin_name']
        admin_desc['username'] = u'admin'
        admin_desc['password'] = request['admin_password']
        admin_desc['name'] = request['admin_name']
        admin_desc['mail_address'] = request['admin_mail_address']
        admin_desc['language'] = language
        admin_desc['role'] =u'admin'
        admin_desc['deletable'] = False
        admin_desc['pgp_key_remove'] = False
        admin_desc['password_change_needed'] = False
        db_create_user(session, state, tid, admin_desc, language)

    receiver_desc = models.User().dict(language)
    receiver_desc['name'] = request['receiver_name']
    receiver_desc['username'] = u'recipient'
    receiver_desc['name'] = request['receiver_name']
    receiver_desc['mail_address'] = request['receiver_mail_address']
    receiver_desc['language'] = language
    receiver_desc['role'] =u'receiver'
    receiver_desc['deletable'] = True
    receiver_desc['pgp_key_remove'] = False
    receiver_desc['can_edit_general_settings'] = not create_admin

    _, receiver = db_create_receiver_user(session, state, tid, receiver_desc, language)

    context_desc = models.Context().dict(language)
    context_desc['name'] = u'Default'
    context_desc['receivers'] = [receiver.id]

    db_create_context(session, state, tid, context_desc, language)

    db_refresh_memory_variables(session, [tid])


@transact
def wizard(session, state, tid, request, create_admin, client_using_tor, language):
    db_wizard(session, state, tid, request, create_admin, client_using_tor, language)


class Wizard(BaseHandler):
    """
    Setup Wizard handler
    """
    check_roles = 'unauthenticated'
    invalidate_cache = True

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.WizardDesc)

        return wizard(self.state, self.request.tid, request, True, self.request.client_using_tor, self.request.language)
