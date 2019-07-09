# -*- coding: utf-8 -*-
#
# Validates the token for password reset changes
from datetime import datetime, timedelta
from sqlalchemy import or_
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.sessions import Sessions
from globaleaks.state import State
from globaleaks.utils.crypto import generateRandomKey
from globaleaks.utils.utility import datetime_now


@transact
def validate_password_reset(session, tid, reset_token):
    """Retrieves a user given a password reset validation token"""
    user = session.query(models.User).filter(
        models.User.reset_password_token == reset_token,
        models.User.reset_password_date >= datetime.now() - timedelta(hours=72)
    ).one_or_none()

    if user is None:
        return

    # Token is used, void it out
    user.reset_password_token = None
    user.reset_password_date = datetime_now()
    user.password_change_needed = True

    session = Sessions.new(tid, user.id, user.tid, user.role, user.password_change_needed, '')

    return session.id


@transact
def generate_password_reset_token(session, state, tid, username_or_email, allow_admin_reset=False):
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
        if not allow_admin_reset and user.role == u'admin':
            continue

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


class PasswordResetHandler(BaseHandler):
    check_roles = 'unauthenticated'
    redirect_url = "/#/login/passwordreset/failure"

    @inlineCallbacks
    def get(self, reset_token):
        auth_token = yield validate_password_reset(self.request.tid,
                                                   reset_token)
        if auth_token:
            self.redirect_url = "/#/login?token=%s" % auth_token

        self.redirect(self.redirect_url)

    def post(self):
        if State.tenant_cache[self.request.tid]['enable_password_reset'] is False:
            return

        request = self.validate_message(self.request.content.read(),
                                        requests.PasswordResetDesc)

        return generate_password_reset_token(self.state,
                                             self.request.tid,
                                             request['username_or_email'])
