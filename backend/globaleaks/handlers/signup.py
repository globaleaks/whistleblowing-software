# -*- coding: utf-8
#
# Handlers implementing platform signup
import copy

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.tenant import db_preallocate as db_preallocate_tenant,\
    db_initialize as db_initialize_tenant
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.wizard import db_wizard
from globaleaks.models import config
from globaleaks.orm import transact
from globaleaks.rest import requests, errors, apicache
from globaleaks.utils.security import generateRandomKey
from globaleaks.utils.utility import datetime_to_ISO8601


def serialize_signup(signup):
    return {
        'name': signup.name,
        'surname': signup.surname,
        'role': signup.role,
        'email': signup.email,
        'phone': signup.phone,
        'subdomain': signup.subdomain,
        'language': signup.language,
        'activation_token': signup.activation_token,
        'registration_date': datetime_to_ISO8601(signup.registration_date),
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
def signup(session, state, tid, request, language):
    node = config.ConfigFactory(session, 1, 'node')

    if not node.get_val(u'enable_signup'):
        raise errors.ForbiddenOperation

    request['activation_token'] = generateRandomKey(32)
    request['language'] = language

    tenant_id = db_preallocate_tenant(session, {'label': request['subdomain'],
                                                'subdomain': request['subdomain']}).id

    signup = models.Signup(request)

    signup.tid = tenant_id

    session.add(signup)

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

    state.format_and_send_mail(session, 1, {'mail_address': signup.email}, template_vars)

    # Email 2 - Admin Notification
    for user_desc in db_get_admin_users(session, 1):
        template_vars = {
            'type': 'admin_signup_alert',
            'signup': serialize_signup(signup),
            'node': db_admin_serialize_node(session, 1, user_desc['language']),
            'notification': db_get_notification(session, 1, user_desc['language']),
            'user': user_desc,
            'signup': signup_dict
        }

        state.format_and_send_mail(session, 1, user_desc, template_vars)


@transact
def signup_activation(session, state, tid, token, language):
    node = config.ConfigFactory(session, 1, 'node')

    if not node.get_val(u'enable_signup'):
        raise errors.ForbiddenOperation

    signup = session.query(models.Signup).filter(models.Signup.activation_token == token).one_or_none()
    if signup is None:
        return {}

    if not session.query(models.Config).filter(models.Config.tid == signup.tid).count():
        tenant = session.query(models.Tenant).filter(models.Tenant.id == signup.tid).one()

        mode = node.get_val('mode')

        db_initialize_tenant(session, tenant, mode)

        password_admin = generateRandomKey(16)
        password_recipient = generateRandomKey(16)

        wizard = {
            'node_language': signup.language,
            'node_name': signup.subdomain,
            'admin_name': signup.name + ' ' + signup.surname,
            'admin_password': password_admin,
            'admin_mail_address': signup.email,
            'receiver_name': signup.name + ' ' + signup.surname,
            'receiver_password': password_recipient,
            'receiver_mail_address': signup.email,
            'profile': 'default',
            'enable_developers_exception_notification': True
        }

        db_wizard(session, state, signup.tid, wizard, False, language)

        ids = [r[0] for r in session.query(models.User.id).filter(models.UserTenant.user_id == models.User.id,
                                                                  models.UserTenant.tenant_id == signup.tid)]

        template_vars = {
            'type': 'activation',
            'node': db_admin_serialize_node(session, 1, language),
            'notification': db_get_notification(session, 1, language),
            'signup': serialize_signup(signup),
            'password_admin': password_admin,
            'password_recipient': password_recipient
        }

        state.format_and_send_mail(session, 1, {'mail_address': signup.email}, template_vars)


class Signup(BaseHandler):
    """
    Signup handler
    """
    check_roles = 'unauthenticated'
    invalidate_cache = True
    root_tenant_only = True

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.SignupDesc)

        if self.state.tenant_cache[1].signup_fingerprint:
            request['client_ip_address'] = self.request.client_ip
            request['client_user_agent'] = self.request.client_ua

        return signup(self.state, self.request.tid, request, self.request.language)


class SignupActivation(BaseHandler):
  """
  Signup handler
  """
  check_roles = 'unauthenticated'
  invalidate_cache = True

  def get(self, token):
      ret = signup_activation(self.state, self.request.tid, token, self.request.language)

      # invalidate also cache of tenant 1
      apicache.ApiCache.invalidate(1)

      self.state.refresh_tenant_state()

      return ret
