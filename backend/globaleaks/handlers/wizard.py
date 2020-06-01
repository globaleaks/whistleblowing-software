# -*- coding: utf-8
#
# Handlers implementing platform wizard
from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.admin.context import db_create_context
from globaleaks.handlers.admin.node import db_update_enabled_languages
from globaleaks.handlers.admin.user import db_create_user
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import config, profiles
from globaleaks.orm import tw
from globaleaks.rest import requests, errors
from globaleaks.utils.crypto import Base64Encoder, GCE
from globaleaks.utils.utility import datetime_now
from globaleaks.utils.log import log


def db_gen_user_keys(session, tid, user, password):
    """
    Transaction generating and saving user keys

    :param session: An ORM session
    :param tid: A tenant ID
    :param user: A user object
    :param password: A user's password
    :return: A private key generated for the user
    """
    enc_key = GCE.derive_key(password.encode(), user.salt)
    crypto_prv_key, user.crypto_pub_key = GCE.generate_keypair()
    user.crypto_bkp_key, user.crypto_rec_key = GCE.generate_recovery_key(crypto_prv_key)
    user.crypto_prv_key = Base64Encoder.encode(GCE.symmetric_encrypt(enc_key, crypto_prv_key))

    # Create an escrow backup for the root tenant
    tid_1_escrow = config.ConfigFactory(session, 1).get_val('crypto_escrow_pub_key')
    if tid_1_escrow:
        user.crypto_escrow_bkp1_key = Base64Encoder.encode(GCE.asymmetric_encrypt(tid_1_escrow, crypto_prv_key))

    # Create an escrow backup for the actual tenant
    tid_n_escrow = config.ConfigFactory(session, tid).get_val('crypto_escrow_pub_key')
    if tid_n_escrow:
        user.crypto_escrow_bkp2_key = Base64Encoder.encode(GCE.asymmetric_encrypt(tid_n_escrow, crypto_prv_key))

    return crypto_prv_key


def db_wizard(session, tid, hostname, request):
    """
    Transaction for the handling of wizard request

    :param session: An ORM session
    :param tid: A tenant ID
    :param request: A user request
    """
    language = request['node_language']

    root_tenant_node = config.ConfigFactory(session, 1)
    encryption = root_tenant_node.get_val('encryption')
    escrow = root_tenant_node.get_val('escrow')

    if tid == 1:
        node = root_tenant_node
    else:
        node = config.ConfigFactory(session, tid)

    if node.get_val('wizard_done'):
        log.err("DANGER: Wizard already initialized!", tid=tid)
        raise errors.ForbiddenOperation

    db_update_enabled_languages(session, tid, [language], language)

    node.set_val('encryption', encryption)
    node.set_val('escrow', escrow)

    node.set_val('name', request['node_name'])
    node.set_val('default_language', language)
    node.set_val('wizard_done', True)
    node.set_val('enable_developers_exception_notification', request['enable_developers_exception_notification'])
    node.set_val('hostname', hostname)

    node_l10n = config.ConfigL10NFactory(session, tid)
    node_l10n.set_val('header_title_prefix', language, request['node_name'])

    profiles.load_profile(session, tid, request['profile'])

    if encryption:
        crypto_escrow_prv_key, crypto_escrow_pub_key = GCE.generate_keypair()
        node.set_val('crypto_escrow_pub_key', crypto_escrow_pub_key)

    admin_desc = models.User().dict(language)
    admin_desc['username'] = request['admin_username']
    admin_desc['name'] = request['admin_name']
    admin_desc['password'] = request['admin_password']
    admin_desc['name'] = request['admin_name']
    admin_desc['mail_address'] = request['admin_mail_address']
    admin_desc['language'] = language
    admin_desc['role'] = 'admin'
    admin_desc['pgp_key_remove'] = False

    admin_user = db_create_user(session, tid, admin_desc, language)
    admin_user.password = GCE.hash_password(request['admin_password'], admin_user.salt)
    admin_user.password_change_needed = False
    admin_user.password_change_date = datetime_now()

    if encryption:
        db_gen_user_keys(session, tid, admin_user, request['admin_password'])
        admin_user.crypto_escrow_prv_key = Base64Encoder.encode(GCE.asymmetric_encrypt(admin_user.crypto_pub_key, crypto_escrow_prv_key))

    receiver_user = None
    if not request['skip_recipient_account_creation']:
        receiver_desc = models.User().dict(language)
        receiver_desc['username'] = request['receiver_username']
        receiver_desc['name'] = request['receiver_name']
        receiver_desc['password'] = request['receiver_password']
        receiver_desc['mail_address'] = request['receiver_mail_address']
        receiver_desc['language'] = language
        receiver_desc['role'] = 'receiver'
        receiver_desc['pgp_key_remove'] = False
        receiver_desc['send_account_activation_link'] = receiver_desc['password'] == ''
        receiver_user = db_create_user(session, tid, receiver_desc, language)

        if receiver_desc['password']:
            receiver_user.password = GCE.hash_password(receiver_desc['password'], receiver_user.salt)

            if encryption:
                db_gen_user_keys(session, tid, receiver_user, receiver_desc['password'])

    context_desc = models.Context().dict(language)
    context_desc['name'] = 'Default'
    context_desc['status'] = 'enabled'

    context_desc['receivers'] = [receiver_user.id] if receiver_user else []

    context = db_create_context(session, tid, context_desc, language)

    # Root tenants initialization terminates here

    if tid == 1:
        db_refresh_memory_variables(session, [tid])
        return

    # Secondary tenants initialization starts here

    tenant = models.db_get(session, models.Tenant, models.Tenant.id == tid)
    tenant.label = request['node_name']

    mode = node.get_val('mode')

    if mode != 'default':
        node.set_val('hostname', tenant.subdomain + '.' + root_tenant_node.get_val('rootdomain'))

    if mode in ['whistleblowing.it', 'eat']:
        for varname in ['reachable_via_web',
                        'enable_receipt_hint',
                        'disable_privacy_badge',
                        'simplified_login',
                        'can_delete_submission',
                        'can_postpone_expiration',
                        'anonymize_outgoing_connections',
                        'frame_ancestors',
                        'password_change_period',
                        'default_questionnaire']:
            node.set_val(varname, root_tenant_node.get_val(varname))

        context.questionnaire_id = root_tenant_node.get_val('default_questionnaire')

        # Set data retention policy to 18 months
        context.tip_timetolive = 540

        # Delete the admin user
        request['admin_password'] = ''
        session.delete(admin_user)

        if receiver_user is not None:
            # Enable the recipient user to configure platform general settings
            receiver_user.can_edit_general_settings = True

            # Set the recipient name equal to the node name
            receiver_user.name = receiver_user.public_name = request['node_name']

    # Apply the specific fixes related to whistleblowing.it projects
    if mode == 'whistleblowing.it':
        node.set_val('simplified_login', True)
        node.set_val('tor', False)

    db_refresh_memory_variables(session, [tid])


class Wizard(BaseHandler):
    """
    Setup Wizard handler
    """
    check_roles = 'none'
    invalidate_cache = True

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.WizardDesc)

        if self.request.hostname not in self.state.tenant_hostname_id_map:
            hostname = self.request.hostname
        else:
            hostname = ''

        return tw(db_wizard, self.request.tid, hostname, request)
