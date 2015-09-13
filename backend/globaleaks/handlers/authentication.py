# -*- coding: UTF-8
#
# authentication
# **************
#
# Files collection handlers and utils

from twisted.internet.defer import inlineCallbacks
from storm.expr import And

from globaleaks import security
from globaleaks.models import Node, User
from globaleaks.settings import transact_ro, GLSettings
from globaleaks.models import Receiver, WhistleblowerTip
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks.utils import utility, tempobj
from globaleaks.utils.utility import log
from globaleaks.third_party import rstr

# needed in order to allow UT override
reactor_override = None


class GLSession(tempobj.TempObj):
    def __init__(self, user_id, user_role, user_status):
        self.user_id = user_id
        self.user_role = user_role
        self.user_status = user_status
        tempobj.TempObj.__init__(self,
                                 GLSettings.sessions,
                                 rstr.xeger(r'[A-Za-z0-9]{42}'),
                                 GLSettings.defaults.lifetimes[user_role],
                                 reactor_override)

    def __repr__(self):
        session_string = "%s %s expire in %s" % \
                         (self.user_role, self.user_id, self._expireCall)
        return session_string


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
        min_sleep = failed_attempts if failed_attempts < 42 else 42

        n = failed_attempts * failed_attempts
        if n < 42:
            max_sleep = n
        else:
            max_sleep = 42

        return utility.randint(min_sleep, max_sleep)

    return 0


def update_session(session):
    """
    Returns
            False if no session is found
            True if the session is active and update the session
                via utils/tempobj.TempObj.touch()
    """
    session_obj = GLSettings.sessions.get(session.id, None)

    if not session_obj:
        return False

    session_obj.touch()
    return True


def authenticated(role):
    """
    Decorator for authenticated sessions.
    If the user (could be admin/receiver/wb) is not authenticated, return
    a http 412 error.
    Otherwise, update the current session and then fire :param:`method`.
    """
    def wrapper(method_handler):
        def call_handler(cls, *args, **kwargs):
            """
            If not yet auth, is redirected
            If is logged with the right account, is accepted
            If is logged with the wrong account, is rejected with a special message
            """
            if not cls.current_user:
                raise errors.NotAuthenticated

            update_session(cls.current_user)

            if role == '*' or role == cls.current_user.user_role:
                log.debug("Authentication OK (%s)" % cls.current_user.user_role)
                return method_handler(cls, *args, **kwargs)

            raise errors.InvalidAuthentication

        return call_handler

    return wrapper


def unauthenticated(method_handler):
    """
    Decorator for unauthenticated requests.
    If the user is logged in an authenticated sessions it does refresh the session.
    """
    def call_handler(cls, *args, **kwargs):
        if cls.current_user:
            update_session(cls.current_user)

        return method_handler(cls, *args, **kwargs)

    return call_handler


def get_tor2web_header(request_headers):
    """
    @param request_headers: HTTP headers
    @return: True or False
    content string of X-Tor2Web header is ignored
    """
    key_content = request_headers.get('X-Tor2Web', None)
    return True if key_content else False


def accept_tor2web(role):
    if role == 'wb':
        return GLSettings.memory_copy.tor2web_whistleblower

    elif role == 'receiver':
        return GLSettings.memory_copy.tor2web_receiver

    elif role == 'admin':
        return GLSettings.memory_copy.tor2web_admin

    elif role == 'custodian':
        return GLSettings.memory_copy.tor2web_custodian

    else:
        return GLSettings.memory_copy.tor2web_unauth


def transport_security_check(wrapped_handler_role):
    """
    Decorator for enforce a minimum security on the transport mode.
    Tor and Tor2web has two different protection level, and some operation
    maybe forbidden if in Tor2web, return 417 (Expectation Fail)
    """
    def wrapper(method_handler):
        def call_handler(cls, *args, **kwargs):
            """
            GLSettings contain the copy of the latest admin configuration, this
            enhance performance instead of searching in te DB at every handler
            connection.
            """
            tor2web_roles = ['wb', 'receiver', 'admin', 'custodian', 'unauth']

            assert wrapped_handler_role in tor2web_roles

            using_tor2web = get_tor2web_header(cls.request.headers)

            if using_tor2web and not accept_tor2web(wrapped_handler_role):
                log.err("Denied request on Tor2web for role %s and resource '%s'" %
                        (wrapped_handler_role, cls.request.uri))
                raise errors.TorNetworkRequired

            if using_tor2web:
                log.debug("Accepted request on Tor2web for role '%s' and resource '%s'" %
                          (wrapped_handler_role, cls.request.uri))

            return method_handler(cls, *args, **kwargs)

        return call_handler

    return wrapper


@transact_ro  # read only transact; manual commit on success needed
def login_wb(store, receipt, using_tor2web):
    """
    Login wb return the WhistleblowerTip.id
    """
    node = store.find(Node).one()
    hashed_receipt = security.hash_password(receipt, node.receipt_salt)
    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.receipt_hash == unicode(hashed_receipt)).one()

    if not wb_tip:
        log.debug("Whistleblower login: Invalid receipt")
        GLSettings.failed_login_attempts += 1
        raise errors.InvalidAuthentication

    if using_tor2web and not accept_tor2web('wb'):
        log.err("Denied login request on Tor2web for role 'wb'")
        raise errors.TorNetworkRequired
    else:
        log.debug("Accepted login request on Tor2web for role 'wb'")

    log.debug("Whistleblower login: Valid receipt")
    wb_tip.last_access = utility.datetime_now()
    store.commit()  # the transact was read only! on success we apply the commit()
    return wb_tip.id


@transact_ro  # read only transact; manual commit on success needed
def login(store, username, password, using_tor2web):
    """
    login returns a tuple (user_id, state, pcn)
    """
    user = store.find(User, And(User.username == username,
                                User.state != u'disabled')).one()

    if not user or not security.check_password(password,  user.password, user.salt):
        log.debug("Login: Invalid credentials")
        GLSettings.failed_login_attempts += 1
        raise errors.InvalidAuthentication

    if using_tor2web and not accept_tor2web(user.role):
        log.err("Denied login request on Tor2web for role '%s'" % user.role)
        raise errors.TorNetworkRequired
    else:
        log.debug("Accepted login request on Tor2web for role '%s'" % user.role)

    log.debug("Login: Success (%s)" % user.role)
    user.last_login = utility.datetime_now()
    store.commit()  # the transact was read only! on success we apply the commit()
    return user.id, user.state, user.role, user.password_change_needed


class AuthenticationHandler(BaseHandler):
    """
    Login handler for admins and receivers
    """
    session_id = None

    def generate_session(self, user_id, role, status):
        session = GLSession(user_id, role, status)
        self.session_id = session.id
        return session

    @authenticated('*')
    def get(self):
        if self.current_user and self.current_user.id not in GLSettings.sessions:
            raise errors.NotAuthenticated

        auth_answer = {
            'session_id': self.current_user.id,
            'role': self.current_user.user_role,
            'user_id': self.current_user.user_id,
            'session_expiration': int(self.current_user.getTime()),
            'status': self.current_user.user_status,
            'password_change_needed': False
        }

        self.write(auth_answer)

    @unauthenticated
    @inlineCallbacks
    def post(self):
        """
        Login
        """
        request = self.validate_message(self.request.body, requests.AuthDesc)

        username = request['username']
        password = request['password']

        delay = random_login_delay()
        if delay:
            yield utility.deferred_sleep(delay)

        using_tor2web = get_tor2web_header(self.request.headers)

        user_id, status, role, pcn = yield login(username, password, using_tor2web)

        yield self.uniform_answers_delay()

        session = self.generate_session(user_id, role, status)

        auth_answer = {
            'role': role,
            'session_id': session.id,
            'user_id': session.user_id,
            'session_expiration': int(GLSettings.sessions[session.id].getTime()),
            'status': session.user_status,
            'password_change_needed': pcn,
        }

        self.write(auth_answer)

    @authenticated('*')
    def delete(self):
        """
        Logout
        """
        if self.current_user:
            try:
                del GLSettings.sessions[self.current_user.id]
            except KeyError:
                raise errors.NotAuthenticated

        self.set_status(200)
        self.finish()


class ReceiptAuthHandler(AuthenticationHandler):
    @unauthenticated
    @inlineCallbacks
    def post(self):
        """
        Login
        """
        request = self.validate_message(self.request.body, requests.ReceiptAuthDesc)

        receipt = request['receipt']

        delay = random_login_delay()
        if delay:
            yield utility.deferred_sleep(delay)

        using_tor2web = get_tor2web_header(self.request.headers)

        user_id = yield login_wb(receipt, using_tor2web)

        yield self.uniform_answers_delay()

        session = self.generate_session(user_id, 'wb', 'Enabled')

        auth_answer = {
            'role': 'wb',
            'session_id': session.id,
            'user_id': session.user_id,
            'session_expiration': int(GLSettings.sessions[session.id].getTime()),
        }

        self.write(auth_answer)
