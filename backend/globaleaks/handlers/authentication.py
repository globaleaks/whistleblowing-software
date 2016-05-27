# -*- coding: UTF-8
#
# authentication
# **************
#
# Files collection handlers and utils

from twisted.internet.defer import inlineCallbacks, returnValue
from storm.expr import And

from globaleaks import security
from globaleaks.orm import transact, transact_ro
from globaleaks.models import User
from globaleaks.settings import GLSettings
from globaleaks.models import InternalTip
from globaleaks.handlers.base import BaseHandler, GLSessions, GLSession
from globaleaks.rest import errors, requests
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


@transact_ro  # read only transact; manual commit on success needed
def login_whistleblower(store, receipt_hash, using_tor2web):
    """
    login_whistleblower returns the InternalTip.id
    """
    wbtip = store.find(InternalTip,
                       InternalTip.receipt_hash == receipt_hash).one()

    if not wbtip:
        log.debug("Whistleblower login: Invalid receipt")
        GLSettings.failed_login_attempts += 1
        raise errors.InvalidAuthentication

    if using_tor2web and not GLSettings.memory_copy.accept_tor2web_access['whistleblower']:
        log.err("Denied login request on Tor2web for role 'whistleblower'")
        raise errors.TorNetworkRequired
    else:
        log.debug("Accepted login request on Tor2web for role 'whistleblower'")

    log.debug("Whistleblower login: Valid receipt")
    wbtip.last_access = datetime_now()
    store.commit()  # the transact was read only! on success we apply the commit()
    return wbtip.id


class AuthenticationHandler(BaseHandler):
    """
    Login handler for admins and recipents and custodians
    """
    handler_exec_time_threshold = 60

    @BaseHandler.authenticated('*')
    def get(self):
        if self.current_user and self.current_user.id not in GLSessions:
            raise errors.NotAuthenticated

        self.write({
            'session_id': self.current_user.id,
            'role': self.current_user.user_role,
            'user_id': self.current_user.user_id,
            'session_expiration': int(self.current_user.getTime()),
            'status': self.current_user.user_status,
            'password_change_needed': False
        })

    @transact
    def step1(self, store, request):
        username = request['username']

        using_tor2web = self.check_tor2web()

        user = store.find(User, And(User.username == username,
                                    User.state != u'disabled')).one()

        if not user:
            log.debug("Login: Invalid credentials")
            GLSettings.failed_login_attempts += 1
            raise errors.InvalidAuthentication

        if using_tor2web and not GLSettings.memory_copy.accept_tor2web_access[user.role]:
            log.err("Denied login request on Tor2web for role '%s'" % user.role)
            raise errors.TorNetworkRequired
        else:
            log.debug("Accepted login request on Tor2web for role '%s' (STEP1)" % user.role)

        return ({
            'salt': user.salt,
            'authentication_m': 14
        })

    @transact
    def step2(self, store, request):
        username = request['username']
        password_hash = request['password_hash']

        using_tor2web = self.check_tor2web()

        #
        user = store.find(User, And(User.username == username,
                                    User.state != u'disabled')).one()

        if not user or password_hash != user.password:
            log.debug("Login: Invalid credentials")
            GLSettings.failed_login_attempts += 1
            raise errors.InvalidAuthentication

        if using_tor2web and not GLSettings.memory_copy.accept_tor2web_access[user.role]:
            log.err("Denied login request on Tor2web for role '%s'" % user.role)
            raise errors.TorNetworkRequired
        else:
            log.debug("Accepted login request on Tor2web for role '%s' (STEP 2)" % user.role)

        log.debug("Login: Success (%s)" % user.role)
        user.last_login = datetime_now()

        session = GLSession(user.id, user.role, user.state)

        return({
            'session_id': session.id,
            'role': session.user_role,
            'user_id': session.user_id,
            'session_expiration': int(session.getTime()),
            'status': session.user_status,
            'password_change_needed': user.password_change_needed
        })

    @BaseHandler.unauthenticated
    @inlineCallbacks
    def post(self):
        """
        Login
        """
        request = self.validate_message(self.request.body, requests.AuthDesc)

        step = request['step']

        delay = random_login_delay()
        if delay:
            yield deferred_sleep(delay)

        try:
            if step == 1:
                ret = yield self.step1(request)
            elif step == 2:
                ret = yield self.step2(request)
        finally:
            yield self.uniform_answers_delay()

        self.write(ret)

    @BaseHandler.authenticated('*')
    def delete(self):
        """
        Logout
        """
        if self.current_user:
            try:
                del GLSessions[self.current_user.id]
            except KeyError:
                raise errors.NotAuthenticated


class ReceiptAuthHandler(AuthenticationHandler):
    handler_exec_time_threshold = 60

    @BaseHandler.unauthenticated
    @inlineCallbacks
    def post(self):
        """
        Receipt login handler used by whistleblowers
        """
        request = self.validate_message(self.request.body, requests.ReceiptAuthDesc)

        receipt_hash = request['receipt_hash']

        delay = random_login_delay()
        if delay:
            yield deferred_sleep(delay)

        using_tor2web = self.check_tor2web()

        try:
            user_id = yield login_whistleblower(receipt_hash, using_tor2web)
        finally:
            yield self.uniform_answers_delay()

        session = GLSession(user_id, 'whistleblower', 'Enabled')

        self.write({
            'session_id': session.id,
            'role': session.user_role,
            'user_id': session.user_id,
            'session_expiration': int(session.getTime())
        })
