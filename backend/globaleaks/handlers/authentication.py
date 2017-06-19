# -*- coding: UTF-8
#
# authentication
# **************
#
# Files collection handlers and utils

from storm.expr import And
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import security
from globaleaks.handlers.base import BaseHandler, GLSessions, GLSession
from globaleaks.models import User
from globaleaks.models import WhistleblowerTip
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import datetime_now, deferred_sleep, log, randint


def random_login_delay():
    """
    in case of failed_login_attempts introduces
    an exponential increasing delay between 0 and 42 seconds

        the function implements the following table:
            ----------------------------------
           | failed_attempts |      delay     |
           | x < 5           | 0              |
           | 5               | random(5, 25)  |
           | 6               | random(6, 36)  |
           | 7               | random(7, 42)  |
           | 8 <= x <= 42    | random(x, 42)  |
           | x > 42          | 42             |
            ----------------------------------
    """
    failed_attempts = GLSettings.failed_login_attempts

    if failed_attempts >= 5:
        n = failed_attempts * failed_attempts

        min_sleep = failed_attempts if failed_attempts < 42 else 42
        max_sleep = n if n < 42 else 42

        return randint(min_sleep, max_sleep)

    return 0


@transact
def login_whistleblower(store, receipt, client_using_tor):
    """
    login_whistleblower returns the WhistleblowerTip.id
    """
    hashed_receipt = security.hash_password(receipt, GLSettings.memory_copy.private.receipt_salt)
    wbtip = store.find(WhistleblowerTip,
                       WhistleblowerTip.receipt_hash == unicode(hashed_receipt)).one()

    if not wbtip:
        log.debug("Whistleblower login: Invalid receipt")
        GLSettings.failed_login_attempts += 1
        raise errors.InvalidAuthentication

    if not client_using_tor and not GLSettings.memory_copy.accept_tor2web_access['whistleblower']:
        log.err("Denied login request over clear Web for role 'whistleblower'")
        raise errors.TorNetworkRequired

    log.debug("Whistleblower login: Valid receipt")
    wbtip.last_access = datetime_now()
    return wbtip.id


@transact
def login(store, username, password, client_using_tor):
    """
    login returns a tuple (user_id, state, pcn)
    """
    user = store.find(User, And(User.username == username,
                                User.state != u'disabled')).one()

    if not user or not security.check_password(password, user.salt, user.password):
        log.debug("Login: Invalid credentials")
        GLSettings.failed_login_attempts += 1
        raise errors.InvalidAuthentication

    if not client_using_tor and not GLSettings.memory_copy.accept_tor2web_access[user.role]:
        log.err("Denied login request over Web for role '%s'" % user.role)
        raise errors.TorNetworkRequired

    log.debug("Login: Success (%s)" % user.role)
    user.last_login = datetime_now()
    return user.id, user.state, user.role, user.password_change_needed


class AuthenticationHandler(BaseHandler):
    """
    Login handler for admins and recipents and custodians
    """
    check_roles = 'unauthenticated'
    uniform_answer_time = True

    @inlineCallbacks
    def post(self):
        """
        Login
        """
        request = self.validate_message(self.request.content.read(), requests.AuthDesc)

        username = request['username']
        password = request['password']

        user_id, status, role, pcn = yield login(username, password, self.request.client_using_tor)

        # Revoke all other sessions for the newly authenticated user
        GLSessions.revoke_all_sessions(user_id)

        session = GLSession(user_id, role, status)

        returnValue({
            'session_id': session.id,
            'role': session.user_role,
            'user_id': session.user_id,
            'session_expiration': int(session.getTime()),
            'status': session.user_status,
            'password_change_needed': pcn
        })


class ReceiptAuthHandler(BaseHandler):
    check_roles = 'unauthenticated'
    uniform_answer_time = True

    @inlineCallbacks
    def post(self):
        """
        Receipt login handler used by whistleblowers
        """
        request = self.validate_message(self.request.content.read(), requests.ReceiptAuthDesc)

        receipt = request['receipt']

        delay = random_login_delay()
        if delay:
            yield deferred_sleep(delay)

        user_id = yield login_whistleblower(receipt, self.request.client_using_tor)

        GLSessions.revoke_all_sessions(user_id)

        session = GLSession(user_id, 'whistleblower', 'Enabled')

        returnValue({
            'session_id': session.id,
            'role': session.user_role,
            'user_id': session.user_id,
            'session_expiration': int(session.getTime())
        })


class SessionHandler(BaseHandler):
    """
    Session handler for authenticated users
    """
    check_roles = {'admin','receiver','custodian','whistleblower'}

    def get(self):
        """
        Refresh and retrive session
        """

        return {
            'session_id': self.current_user.id,
            'role': self.current_user.user_role,
            'user_id': self.current_user.user_id,
            'session_expiration': int(self.current_user.getTime()),
            'status': self.current_user.user_status,
            'password_change_needed': False
        }

    def delete(self):
        """
        Logout
        """
        del GLSessions[self.current_user.id]
