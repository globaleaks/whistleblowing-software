# -*- coding: utf-8
#
# Handlers implementing platform signup
from sqlalchemy import not_
from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.tenant import db_preallocate_tenant as db_preallocate_tenant,\
    db_initialize_tenant, db_refresh_memory_variables
from globaleaks.handlers.admin.user import db_get_users
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.wizard import db_wizard
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.crypto import generateRandomKey, generateRandomPassword


def serialize_signup(signup):
    """
    Transaction serializing the signup descriptor

    :param signup: A signup model
    :return: A serialization of the provided model
    """
    return {
        'name': signup.name,
        'surname': signup.surname,
        'role': signup.role,
        'email': signup.email,
        'phone': signup.phone,
        'subdomain': signup.subdomain,
        'language': signup.language,
        'activation_token': signup.activation_token,
        'registration_date': signup.registration_date,
        'use_case': signup.use_case,
        'use_case_other': signup.use_case_other,
        'organization_name': signup.organization_name,
        'organization_type': signup.organization_type,
        'organization_location1': signup.organization_location1,
        'organization_location2': signup.organization_location2,
        'organization_location3': signup.organization_location3,
        'organization_location4': signup.organization_location4,
        'organization_site': signup.organization_site,
        'organization_number_employees': signup.organization_number_employees,
        'organization_number_users': signup.organization_number_users,
        'hear_channel': signup.hear_channel,
        'tos1': signup.tos1,
        'tos2': signup.tos2
    }


@transact
def signup(session, request, language):
    """
    Transact handling the registration of a new signup

    :param session: An ORM session
    :param request: A user request
    :param language: A language of the request
    """
    config = ConfigFactory(session, 1)

    if not config.get_val('enable_signup'):
        raise errors.ForbiddenOperation

    request['activation_token'] = generateRandomKey()
    request['language'] = language

    # Delete the tenants created for the same subdomain that have still not been activated
    # Ticket reference: https://github.com/globaleaks/GlobaLeaks/issues/2640
    subquery = session.query(models.Tenant.id) \
                      .filter(models.Signup.subdomain == request['subdomain'],
                              not_(models.Signup.activation_token.is_(None)),
                              models.Tenant.id == models.Signup.tid,
                              models.Tenant.subdomain == models.Signup.subdomain) \
                      .subquery()

    session.query(models.Tenant).filter(models.Tenant.id.in_(subquery)).delete(synchronize_session=False)

    tenant_id = db_preallocate_tenant(session, {'label': request['subdomain'],
                                                'subdomain': request['subdomain']}).id

    signup = models.Signup(request)

    signup.tid = tenant_id

    session.add(signup)

    session.flush()

    # We need to send two emails
    #
    # The first one is sent to the platform owner with the activation email.
    #
    # The second goes to the instance administrators notifying them that a new
    # platform has been added.

    signup_dict = serialize_signup(signup)

    # Email 1 - Activation Link
    template_vars = {
        'type': 'signup',
        'node': db_admin_serialize_node(session, 1, language),
        'notification': db_get_notification(session, 1, language),
        'signup': signup_dict
    }

    State.format_and_send_mail(session, 1, {'mail_address': signup.email}, template_vars)

    # Email 2 - Admin Notification
    for user_desc in db_get_users(session, 1, 'admin'):
        template_vars = {
            'type': 'admin_signup_alert',
            'node': db_admin_serialize_node(session, 1, user_desc['language']),
            'notification': db_get_notification(session, 1, user_desc['language']),
            'user': user_desc,
            'signup': signup_dict
        }

        State.format_and_send_mail(session, 1, user_desc, template_vars)


@transact
def signup_activation(session, token, hostname, language):
    """
    Transaction registering the activation of a platform registered via signup

    :param session: An ORM session
    :param token: A activation token
    :param language: A language of the request
    """
    config = ConfigFactory(session, 1)

    if not config.get_val('enable_signup'):
        raise errors.ForbiddenOperation

    ret = session.query(models.Signup, models.Tenant) \
                 .filter(models.Signup.activation_token == token,
                         models.Tenant.id == models.Signup.tid).one_or_none()

    if ret is None:
        return {}

    signup, tenant = ret[0], ret[1]

    signup.activation_token = None

    mode = config.get_val('mode')

    db_initialize_tenant(session, tenant, mode)

    password_admin = generateRandomPassword(16)
    password_receiver = generateRandomPassword(16)

    node_name = signup.organization_name if signup.organization_name else signup.subdomain

    wizard = {
        'node_language': signup.language,
        'node_name': node_name,
        'admin_username': 'admin',
        'admin_name': signup.name + ' ' + signup.surname,
        'admin_password': password_admin,
        'admin_mail_address': signup.email,
        'receiver_username': 'recipient',
        'receiver_name': signup.name + ' ' + signup.surname,
        'receiver_password': password_receiver,
        'receiver_mail_address': signup.email,
        'profile': 'default',
        'skip_recipient_account_creation': False,
        'enable_developers_exception_notification': True
    }

    db_wizard(session, signup.tid, hostname, wizard)

    template_vars = {
        'type': 'activation',
        'node': db_admin_serialize_node(session, 1, language),
        'notification': db_get_notification(session, 1, language),
        'signup': serialize_signup(signup),
        'password_admin': wizard['admin_password'],
        'password_recipient': wizard['receiver_password']
    }

    State.format_and_send_mail(session, 1, {'mail_address': signup.email}, template_vars)

    db_refresh_memory_variables(session, [signup.tid])


class Signup(BaseHandler):
    """
    Signup handler responsible of registration
    """
    check_roles = 'none'
    invalidate_cache = False
    root_tenant_only = True

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.SignupDesc)

        request['client_ip_address'] = self.request.client_ip
        request['client_user_agent'] = self.request.client_ua

        return signup(request, self.request.language)


class SignupActivation(BaseHandler):
    """
    Signup handler responsible of activation
    """
    check_roles = 'none'
    invalidate_cache = False
    root_tenant_only = True
    refresh_connection_endpoints = True

    def get(self, token):
        return signup_activation(token, self.request.hostname, self.request.language)
