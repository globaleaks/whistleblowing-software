# -*- coding: utf-8 -*-
#
# Handlers dealing with platform authentication
from datetime import timedelta
from random import SystemRandom
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks.handlers.base import connection_check, BaseHandler
from globaleaks.models import InternalTip, User, WhistleblowerTip
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.sessions import Sessions
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.crypto import totpVerify, Base64Encoder, GCE
from globaleaks.utils.log import log
from globaleaks.utils.utility import datetime_now, deferred_sleep


def login_failure(tid, role, whistleblower=False):
    Settings.failed_login_attempts[tid] = Settings.failed_login_attempts.get(tid, 0) + 1

    State.log(tid=tid, type='whistleblower_login_failure' if whistleblower else 'login_failure')

    raise errors.InvalidAuthentication


def login_delay(tid):
    """
    The function in case of failed_login_attempts introduces
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
    failed_attempts = Settings.failed_login_attempts.get(tid, 0)

    if failed_attempts < 5:
        return

    n = failed_attempts * failed_attempts
    min_sleep = failed_attempts if failed_attempts < 42 else 42
    max_sleep = n if n < 42 else 42

    return deferred_sleep(SystemRandom().randint(min_sleep, max_sleep))


@transact
def login_whistleblower(session, tid, receipt):
    """
    Login transaction for whistleblowers' access

    :param session: An ORM session
    :param tid: A tenant ID
    :param receipt: A provided receipt
    :return: Returns a user session in case of success
    """
    x = None

    algorithms = [x[0] for x in session.query(WhistleblowerTip.hash_alg).filter(WhistleblowerTip.tid == tid).distinct()]

    if algorithms:
        hashes = [GCE.hash_password(receipt, State.tenant_cache[tid].receipt_salt, alg) for alg in algorithms]

        x = session.query(WhistleblowerTip, InternalTip) \
                   .filter(WhistleblowerTip.receipt_hash.in_(hashes),
                           WhistleblowerTip.tid == tid,
                           InternalTip.id == WhistleblowerTip.id).one_or_none()

    if x is None:
        login_failure(tid, 1)

    wbtip = x[0]
    itip = x[1]

    itip.wb_last_access = datetime_now()

    crypto_prv_key = ''
    if wbtip.crypto_prv_key:
        user_key = GCE.derive_key(receipt.encode(), State.tenant_cache[tid].receipt_salt)
        crypto_prv_key = GCE.symmetric_decrypt(user_key, Base64Encoder.decode(wbtip.crypto_prv_key))

    return Sessions.new(tid, wbtip.id, tid, 'whistleblower', False, False, crypto_prv_key, '')


@transact
def login(session, tid, username, password, authcode, client_using_tor, client_ip):
    """
    Login transaction for users' access

    :param session: An ORM session
    :param tid: A tenant ID
    :param username: A provided username
    :param password: A provided password
    :param authcode: A provided authcode
    :param client_using_tor: A boolean signaling Tor usage
    :param client_ip:  The client IP
    :return: Returns a user session in case of success
    """
    user = session.query(User).filter(User.username == username,
                                      User.state == 'enabled',
                                      User.tid == tid).one_or_none()

    if not user or not GCE.check_password(user.hash_alg, password, user.salt, user.password):
        login_failure(tid, 0)


    connection_check(tid, client_ip, user.role, client_using_tor)

    crypto_prv_key = ''
    if user.crypto_prv_key:
        user_key = GCE.derive_key(password.encode(), user.salt)
        crypto_prv_key = GCE.symmetric_decrypt(user_key, Base64Encoder.decode(user.crypto_prv_key))
    elif State.tenant_cache[tid].encryption:
        # Force the password change on which the user key will be created
        user.password_change_needed = True

    # Require password change if password change threshold is exceeded
    if State.tenant_cache[tid].password_change_period > 0 and \
       user.password_change_date < datetime_now() - timedelta(days=State.tenant_cache[tid].password_change_period):
        user.password_change_needed = True

    if user.two_factor_enable:
        if authcode != '':
            # RFC 6238: step size 30 sec; valid_window = 1; total size of the window: 1.30 sec
            try:
                totpVerify(user.two_factor_secret, authcode)
            except:
                raise errors.InvalidTwoFactorAuthCode
        else:
            raise errors.TwoFactorAuthCodeRequired

    user.last_login = datetime_now()

    return Sessions.new(tid, user.id, user.tid, user.role, user.password_change_needed, user.two_factor_enable, crypto_prv_key, user.crypto_escrow_prv_key)


class AuthenticationHandler(BaseHandler):
    """
    Login handler for admins and recipents and custodians
    """
    check_roles = 'any'
    uniform_answer_time = True
    require_token = [b'POST']

    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.content.read(), requests.AuthDesc)

        tid = int(request['tid'])
        if tid == 0:
            tid = self.request.tid

        yield login_delay(tid)

        session = yield login(tid,
                              request['username'],
                              request['password'],
                              request['authcode'],
                              self.request.client_using_tor,
                              self.request.client_ip)

        State.log(tid=tid, type='login', user_id=session.user_id)

        if tid != self.request.tid:
            returnValue({
                'redirect': 'https://%s/#/login?token=%s' % (State.tenant_cache[tid].hostname, session.id)
            })

        returnValue(session.serialize())


class TokenAuthHandler(BaseHandler):
    """
    Login handler for token based authentication
    """
    check_roles = 'any'
    uniform_answer_time = True
    require_token = [b'POST']

    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.content.read(), requests.TokenAuthDesc)

        yield login_delay(self.request.tid)

        session = Sessions.get(request['authtoken'])
        if session is None or session.tid != self.request.tid:
            login_failure(self.request.tid, 0)

        connection_check(self.request.tid, self.request.client_ip,
                         session.user_role, self.request.client_using_tor)

        session = Sessions.regenerate(session.id)

        returnValue(session.serialize())


class ReceiptAuthHandler(BaseHandler):
    """
    Receipt handler used by whistleblowers
    """
    check_roles = 'any'
    require_token = [b'POST']
    uniform_answer_time = True

    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.content.read(), requests.ReceiptAuthDesc)

        yield login_delay(self.request.tid)

        connection_check(self.request.tid, self.request.client_ip,
                         'whistleblower', self.request.client_using_tor)

        session = yield login_whistleblower(self.request.tid, request['receipt'])

        State.log(tid=session.tid,  type='whistleblower_login')

        returnValue(session.serialize())


class SessionHandler(BaseHandler):
    """
    Session handler for authenticated users
    """
    check_roles = {'user', 'whistleblower'}

    def get(self):
        """
        Refresh and retrive session
        """
        return self.session.serialize()

    def delete(self):
        """
        Logout
        """
        if self.session.user_role == 'whistleblower':
            State.log(tid=self.session.tid,  type='whistleblower_logout')
        else:
            State.log(tid=self.session.tid,  type='logout', user_id=self.session.user_id)

        del Sessions[self.session.id]



class TenantAuthSwitchHandler(BaseHandler):
    """
    Login handler for switching tenant
    """
    check_roles = 'admin'

    def get(self, tid):
        if self.request.tid != 1:
            raise errors.InvalidAuthentication

        tid = int(tid)
        session = Sessions.new(tid,
                               self.session.user_id,
                               self.session.user_tid,
                               self.session.user_role,
                               False,
                               True,
                               self.session.cc,
                               self.session.ek,
                               True)

        return {'redirect': '/t/%d/#/login?token=%s' % (tid, session.id)}
