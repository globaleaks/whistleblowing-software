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
from globaleaks.utils.utility import datetime_now, log


def db_wizard(session, state, tid, mode, request, client_using_tor, language):
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

    admin_user = db_create_user(session, state, tid, admin_desc, language)
    admin_user.password_change_needed = False
    admin_user.password_change_date = datetime_now()

    receiver_desc = models.User().dict(language)
    receiver_desc['name'] = request['receiver_name']
    receiver_desc['username'] = u'recipient'
    receiver_desc['password'] = request['receiver_password']
    receiver_desc['name'] = request['receiver_name']
    receiver_desc['mail_address'] = request['receiver_mail_address']
    receiver_desc['language'] = language
    receiver_desc['role'] =u'receiver'
    receiver_desc['deletable'] = True
    receiver_desc['pgp_key_remove'] = False

    _, receiver_user = db_create_receiver_user(session, state, tid, receiver_desc, language)

    context_desc = models.Context().dict(language)
    context_desc['name'] = u'Default'
    context_desc['receivers'] = [receiver_user.id]

    context = db_create_context(session, state, tid, context_desc, language)

    node.set_val(u'mode', mode)

    # Apply the specific fixes related to whistleblowing.it projects
    if mode == u'whistleblowing.it':
        node.set_val(u'hostname', tenant.subdomain + '.' + 'whistleblowing.it')
        node.set_val(u'password_change_period', 365)
        node.set_val(u'disable_key_code_hint', True)
        node.set_val(u'disable_privacy_badge', True)
        node.set_val(u'disable_donation_panel', True)
        node.set_val(u'simplified_login', True)
        node.set_val(u'reachable_via_web', True)
        node.set_val(u'allow_unencrypted', True)
        node.set_val(u'anonymize_outgoing_connections', True)
        node.set_val(u'disable_encryption_warnings', True)
        node.set_val(u'can_delete_submission', False)
        node.set_val(u'enable_user_pgp_key_upload', False)

        # Delete the admin user
        session.delete(admin_user)

        # Set the recipient name equal to the node name
        receiver_user.name = request['node_name']

        # Enable the recipient user to configure platform general settings
        receiver_user.can_edit_general_settings = True

        # Set data retention policy to 18 months
        context.tip_timetolive = 540

        # Enable recipients to load files to the whistleblower
        context.enable_rc_to_wb_files = True

    db_refresh_memory_variables(session, [tid])


@transact
def wizard(session, state, tid, mode, request, client_using_tor, language):
    db_wizard(session, state, tid, mode, request, client_using_tor, language)


class Wizard(BaseHandler):
    """
    Setup Wizard handler
    """
    check_roles = 'unauthenticated'
    invalidate_cache = True

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.WizardDesc)

        return wizard(self.state, self.request.tid, u'default', request, self.request.client_using_tor, self.request.language)
