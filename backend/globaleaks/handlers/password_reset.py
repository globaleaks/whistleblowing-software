# -*- coding: utf-8 -*-
#
# Validates the token for password reset changes

from datetime import datetime, timedelta

from sqlalchemy import or_

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import user_serialize_user

from globaleaks.models import get_auth_token
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.utility import datetime_now
from globaleaks.utils.security import generateRandomKey

from globaleaks.utils.security import hash_password, generateRandomKey


@transact
def validate_password_reset(session, state, tid, reset_token):
    '''transact version of db_validate_address_change'''
    return db_validate_password_reset(session, state, tid, reset_token)


def db_validate_password_reset(session, state, tid, reset_token):
    '''Retrieves a user given a password reset validation token'''
    from globaleaks.handlers.admin.notification import db_get_notification
    from globaleaks.handlers.admin.node import db_admin_serialize_node
    from globaleaks.handlers.admin.user import get_user
    from globaleaks.handlers.user import user_serialize_user

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
    user.auth_token = get_auth_token()

    return user.auth_token


def db_generate_password_reset_token(session, state, tid, username_or_email):
    '''Generates a reset token against the backend, then send email to validate it'''
    from globaleaks.handlers.admin.notification import db_get_notification
    from globaleaks.handlers.admin.node import db_admin_serialize_node
    from globaleaks.handlers.admin.user import get_user
    from globaleaks.handlers.user import user_serialize_user

    users = session.query(models.User).filter(
      or_(models.User.username == username_or_email,
          models.User.mail_address == username_or_email),
      models.User.tid == tid,
      models.User.role != u'admin'
    ).distinct()

    for user in users:
        user.reset_password_token = generateRandomKey(32)
        user.reset_password_date = datetime_now()

        user_desc = user_serialize_user(session, user, user.language)

        template_vars = {
            'type': 'password_reset_validation',
            'user': user_desc,
            'reset_token': user.reset_password_token,
            'node': db_admin_serialize_node(session, 1, user.language),
            'notification': db_get_notification(session, tid, user.language)
        }

        state.format_and_send_mail(session, tid, user_desc, template_vars)


@transact
def generate_password_reset_token(session, state, tid, username_or_email):
    '''transact version of db_generate_password_reset_token'''
    return db_generate_password_reset_token(session, state, tid, username_or_email)


class PasswordResetHandler(BaseHandler):
    check_roles = 'unauthenticated'
    failure_url = "/#/login/passwordreset/failure"

    @inlineCallbacks
    def get(self, reset_token):
        if State.tenant_cache[self.request.tid]['enable_password_reset'] is False:
            self.redirect(self.failure_url)

        auth_token = yield validate_password_reset(self.state,
                                                   self.request.tid,
                                                   reset_token)
        if auth_token:
            self.redirect("/#/login?token=%s" % auth_token)

        self.redirect(self.failure_url)

    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.PasswordResetDesc)

        if State.tenant_cache[self.request.tid]['enable_password_reset'] is False:
            return

        return generate_password_reset_token(self.state,
                                             self.request.tid,
                                             request['username_or_email'])
