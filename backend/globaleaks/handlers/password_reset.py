# -*- coding: utf-8 -*-
#
# Validates the token for password reset changes
from datetime import datetime, timedelta
from sqlalchemy import or_

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.sessions import Sessions
from globaleaks.state import State
from globaleaks.utils.crypto import generateRandomKey, Base32Encoder, GCE
from globaleaks.utils.utility import datetime_now


@transact
def validate_password_reset(session, tid, reset_token, recovery_key):
    """Retrieves a user given a password reset validation token"""
    now = datetime.now()
    prv_key = ''

    user = session.query(models.User).filter(
        models.User.reset_password_token == reset_token,
        models.User.reset_password_date >= now - timedelta(hours=72)
    ).one_or_none()

    # If the authentication token is invalid
    if user is None:
        return {'status': 'invalid_reset_token_provided'}

    # If encryption is enabled require the recovery key
    if user.crypto_prv_key:
        try:
            recovery_key = recovery_key.replace('-', '').upper() + '===='
            recovery_key = Base32Encoder().decode(recovery_key.encode('utf-8'))
            prv_key = GCE.symmetric_decrypt(recovery_key, user.crypto_bkp_key)
        except:
            return {'status': 'invalid_recovery_key_provided'}

    # Token is used, void it out
    user.reset_password_token = None
    user.reset_password_date = now
    user.password_change_needed = True

    session = Sessions.new(tid, user.id, user.tid, user.role,
                           user.password_change_needed, user.two_factor_enable, prv_key)

    return {'status': 'success', 'token': session.id}


@transact
def generate_password_reset_token(session, state, tid, username_or_email):
    from globaleaks.handlers.admin.notification import db_get_notification
    from globaleaks.handlers.admin.node import db_admin_serialize_node
    from globaleaks.handlers.user import user_serialize_user

    users = session.query(models.User).filter(
      or_(models.User.username == username_or_email,
          models.User.mail_address == username_or_email),
      models.UserTenant.user_id == models.User.id,
      models.UserTenant.tenant_id == tid
    ).distinct()

    for user in users:
        user.reset_password_token = generateRandomKey(32)
        user.reset_password_date = datetime_now()

        user_desc = user_serialize_user(session, user, user.language)

        template_vars = {
            'type': 'password_reset_validation',
            'user': user_desc,
            'reset_token': user.reset_password_token,
            'node': db_admin_serialize_node(session, tid, user.language),
            'notification': db_get_notification(session, tid, user.language)
        }

        state.format_and_send_mail(session, tid, user_desc, template_vars)

        return {'redirect': '/login/passwordreset/requested'}


class PasswordResetHandler(BaseHandler):
    check_roles = 'none'

    def post(self):
        if State.tenant_cache[self.request.tid]['enable_password_reset'] is False:
            return

        request = self.validate_message(self.request.content.read(),
                                        requests.PasswordReset1Desc)

        return generate_password_reset_token(self.state,
                                             self.request.tid,
                                             request['username_or_email'])

    def put(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.PasswordReset2Desc)

        return validate_password_reset(self.request.tid,
                                       request['reset_token'],
                                       request['recovery_key'])
