# -*- coding: utf-8 -*-
#
# Validates the token for password reset changes

from datetime import datetime, timedelta

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import user_serialize_user

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
        return False

    # Token is used, void it out
    user.reset_password_token = None
    user.reset_password_date = datetime_now()
    user.password_change_needed = True

    # Set the new password
    user_desc = user_serialize_user(session, user, user.language)
    new_password = generateRandomKey(32)
    pw_hash = hash_password(new_password, user.salt)

    user.password = pw_hash
    session.commit()

    # and now send the new PW
    template_vars = {
        'type': 'password_reset_complete',
        'user': user_desc,
        'new_password': new_password,
        'node': db_admin_serialize_node(session, 1, user.language),
        'notification': db_get_notification(session, tid, user.language)
    }

    state.format_and_send_mail(session, tid, user_desc, template_vars)

    return True

@transact
def generate_password_reset_token(session, state, tid, username, email):
    '''transact version of db_generate_password_reset_token'''
    return db_generate_password_reset_token(session, state, tid, username, email)

def db_generate_password_reset_token(session, state, tid, username, email):
    '''Generates a reset token against the backend, then send email to validate it'''
    from globaleaks.handlers.admin.notification import db_get_notification
    from globaleaks.handlers.admin.node import db_admin_serialize_node
    from globaleaks.handlers.admin.user import get_user
    from globaleaks.handlers.user import user_serialize_user

    user = session.query(models.User).filter(
        models.User.username == username,
        models.User.mail_address == email
    ).one_or_none()

    if user is None:
        return None

    user.reset_password_token = generateRandomKey(32)
    user.reset_password_date = datetime_now()
    session.commit()

    user_desc = user_serialize_user(session, user, user.language)

    template_vars = {
        'type': 'password_reset_validation',
        'user': user_desc,
        'reset_token': user.reset_password_token,
        'node': db_admin_serialize_node(session, 1, user.language),
        'notification': db_get_notification(session, tid, user.language)
    }

    state.format_and_send_mail(session, tid, user_desc, template_vars)

class PasswordResetHandler(BaseHandler):
    check_roles = '*'
    redirect_url = "/#/login/passwordreset/failure"

    @inlineCallbacks
    def get(self, reset_token):
        if State.tenant_cache[self.request.tid]['enable_password_reset'] is False:
            self.redirect(self.redirect_url)

        check = yield validate_password_reset(self.state,
                                              self.request.tid,
                                              reset_token)
        if check:
            self.redirect_url = "/#/login/passwordreset/success"

        self.redirect(self.redirect_url)

    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.content.read(),
                                        requests.PasswordResetDesc)

        if State.tenant_cache[self.request.tid]['enable_password_reset'] is False:
            return

        yield generate_password_reset_token(self.state,
                                            self.request.tid,
                                            request['username'],
                                            request['mail_address'])
