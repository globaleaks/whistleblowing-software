# -*- coding: UTF-8
#
#   authentication
#   **************
#
# Files collection handlers and utils

from twisted.internet.defer import inlineCallbacks
from storm.exceptions import NotOneError
from storm.expr import And

from globaleaks import security
from globaleaks.models import Node, User
from globaleaks.settings import transact_ro, GLSetting
from globaleaks.models import Receiver, WhistleblowerTip
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks.utils import utility, tempobj
from globaleaks.utils.utility import log
from globaleaks.third_party import rstr

# needed in order to allow UT override
reactor = None

class GLSession(tempobj.TempObj):

    def __init__(self, user_id, user_role, user_status):
        self.user_role = user_role
        self.user_id = user_id
        self.user_role = user_role
        self.user_status = user_status
        tempobj.TempObj.__init__(self,
                                 GLSetting.sessions,
                                 rstr.xeger(r'[A-Za-z0-9]{42}'),
                                 GLSetting.defaults.lifetimes[user_role],
                                 reactor)

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
    failed_attempts = GLSetting.failed_login_attempts

    if failed_attempts >= 5:
        min_sleep = failed_attempts if failed_attempts < 42 else 42

        n = failed_attempts * failed_attempts
        if n < 42:
            max_sleep = n
        else:
            max_sleep = 42

        return utility.randint(min_sleep, max_sleep)

    return 0

def update_session(user):
    """
    Returns
            False if no session is found
            True if the session is active and update the session
                via utils/tempobj.TempObj.touch()
    """
    session_obj = GLSetting.sessions.get(user.id, None)

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
                log.debug("Authentication OK (%s)" % cls.current_user.user_role )
                return method_handler(cls, *args, **kwargs)

            error = "Good login in wrong scope: you %s, expected %s" % \
                    (cls.current_user.user_role, role)

            log.err(error)

            raise errors.InvalidScopeAuth(error)

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
        return GLSetting.memory_copy.tor2web_submission

    elif role == 'receiver':
        return GLSetting.memory_copy.tor2web_receiver

    elif role == 'admin':
        return GLSetting.memory_copy.tor2web_admin

    else:
        return GLSetting.memory_copy.tor2web_unauth

def transport_security_check(wrapped_handler_role):
    """
    Decorator for enforce a minimum security on the transport mode.
    Tor and Tor2web has two different protection level, and some operation
    maybe forbidden if in Tor2web, return 417 (Expectation Fail)
    """
    def wrapper(method_handler):
        def call_handler(cls, *args, **kwargs):
            """
            GLSetting contain the copy of the latest admin configuration, this
            enhance performance instead of searching in te DB at every handler
            connection.
            """
            tor2web_roles = ['wb', 'receiver', 'admin', 'unauth']

            assert wrapped_handler_role in tor2web_roles

            are_we_tor2web = get_tor2web_header(cls.request.headers)

            if are_we_tor2web and accept_tor2web(wrapped_handler_role) == False:
                log.err("Denied request on Tor2web for role %s and resource '%s'" %
                    (wrapped_handler_role, cls.request.uri) )
                raise errors.TorNetworkRequired

            if are_we_tor2web:
                log.debug("Accepted request on Tor2web for role '%s' and resource '%s'" %
                    (wrapped_handler_role, cls.request.uri) )

            return method_handler(cls, *args, **kwargs)

        return call_handler
    return wrapper


@transact_ro # read only transact; manual commit on success needed
def login_wb(store, receipt):
    """
    Login wb return the WhistleblowerTip.id
    """
    try:
        node = store.find(Node).one()
        hashed_receipt = security.hash_password(receipt, node.receipt_salt)
        wb_tip = store.find(WhistleblowerTip,
                            WhistleblowerTip.receipt_hash == unicode(hashed_receipt)).one()
    except NotOneError, e:
        # This is one of the fatal error that never need to happen
        log.err("Expected unique fields (receipt) not unique when hashed %s" % receipt)
        return False

    if not wb_tip:
        log.debug("Whistleblower: Invalid receipt")
        return False

    log.debug("Whistleblower: Valid receipt")
    wb_tip.last_access = utility.datetime_now()
    store.commit() # the transact was read only! on success we apply the commit()
    return unicode(wb_tip.id)


@transact_ro  # read only transact; manual commit on success needed
def login_receiver(store, username, password):
    """
    This login receiver need to collect also the amount of unsuccessful
    consecutive logins, because this element may bring to password lockdown.

    login_receiver return the receiver.id
    """
    receiver_user = store.find(User, And(User.username == username, User.state != u'disabled')).one()

    if not receiver_user or receiver_user.role != 'receiver':
        log.debug("Receiver: Fail auth, username %s do not exists" % username)
        return False, None, None

    if not security.check_password(password, receiver_user.password, receiver_user.salt):
        log.debug("Receiver login: Invalid password")
        return False, None, None
    else:
        log.debug("Receiver: Authorized receiver %s" % username)
        receiver_user.last_login = utility.datetime_now()
        receiver = store.find(Receiver, (Receiver.user_id == receiver_user.id)).one()
        store.commit() # the transact was read only! on success we apply the commit()
        return receiver.id, receiver_user.state, receiver_user.password_change_needed

@transact_ro  # read only transact; manual commit on success needed
def login_admin(store, username, password):
    """
    login_admin return the 'username' of the administrator
    """

    admin_user = store.find(User, User.username == username).one()

    if not admin_user or admin_user.role != 'admin':
        log.debug("Receiver: Fail auth, username %s do not exists" % username)
        return False, None, None

    if not security.check_password(password, admin_user.password, admin_user.salt):
        log.debug("Admin login: Invalid password")
        return False, None, None
    else:
        log.debug("Admin: Authorized admin %s" % username)
        admin_user.last_login = utility.datetime_now()
        store.commit() # the transact was read only! on success we apply the commit()
        return username, admin_user.state, admin_user.password_change_needed

class AuthenticationHandler(BaseHandler):
    """
    Login handler
    """
    session_id = None

    def generate_session(self, user_id, role, status):
        """
        Args:
            role: can be either 'admin', 'wb' or 'receiver'

            user_id: will be in the case of the receiver the receiver.id in the
                case of an admin it will be set to 'admin', in the case of the
                'wb' it will be the whistleblower id.
        """
        session = GLSession(user_id, role, status)
        self.session_id = session.id
        return self.session_id

    @authenticated('*')
    def get(self):
        if self.current_user:
            try:
                session = GLSetting.sessions[self.current_user.id]
            except KeyError:
                raise errors.NotAuthenticated

        auth_answer = {
            'session_id': self.current_user.id,
            'role': self.current_user.user_role,
            'user_id': unicode(self.current_user.user_id),
            'session_expiration': int(self.current_user.getTime()),
        }

        self.write(auth_answer)


    @unauthenticated
    @inlineCallbacks
    def post(self):
        """
        This is the /login handler expecting login/password/role,
        """
        request = self.validate_message(self.request.body, requests.authDict)

        username = request['username']
        password = request['password']
        role = request['role']

        delay = random_login_delay()
        if delay:
            yield utility.deferred_sleep(delay)

        if role not in ['admin', 'wb', 'receiver']:
           raise errors.InvalidInputFormat("Authentication role %s" % str(role) )

        if get_tor2web_header(self.request.headers):
            if not accept_tor2web(role):
                log.err("Denied login request on Tor2web for role '%s'" % role)
                raise errors.TorNetworkRequired
            else:
               log.debug("Accepted login request on Tor2web for role '%s'" % role)

        # Then verify credential, if the channel shall be trusted
        #
        # Here is created the session struct, is now explicit in the
        # three roles, because 'user_id' has a different meaning for every role

        if role == 'admin':

            authorized_username, status, pcn = yield login_admin(username, password)
            if authorized_username is False:
                GLSetting.failed_login_attempts += 1
                raise errors.InvalidAuthRequest
            new_session_id = self.generate_session(authorized_username, role, status)

            auth_answer = {
                'role': 'admin',
                'session_id': new_session_id,
                'user_id': unicode(authorized_username),
                'session_expiration': int(GLSetting.sessions[new_session_id].getTime()),
                'status': status,
                'password_change_needed': pcn
            }

        elif role == 'wb':

            wbtip_id = yield login_wb(password)
            if wbtip_id is False:
                GLSetting.failed_login_attempts += 1
                raise errors.InvalidAuthRequest

            new_session_id = self.generate_session(wbtip_id, role, 'enabled')

            auth_answer = {
                'role': 'admin',
                'session_id': new_session_id,
                'user_id': unicode(wbtip_id),
                'session_expiration': int(GLSetting.sessions[new_session_id].getTime()),
                'status': 'enabled',
                'password_change_needed': False
            }

        elif role == 'receiver':

            receiver_id, status, pcn = yield login_receiver(username, password)
            if receiver_id is False:
                GLSetting.failed_login_attempts += 1
                raise errors.InvalidAuthRequest

            new_session_id = self.generate_session(receiver_id, role, status)

            auth_answer = {
                'role': 'receiver',
                'session_id': new_session_id,
                'user_id': unicode(receiver_id),
                'session_expiration': int(GLSetting.sessions[new_session_id].getTime()),
                'status': status,
                'password_change_needed': pcn
            }

        else:

            log.err("Invalid role proposed to authenticate!")
            raise errors.InvalidAuthRequest

        yield self.uniform_answers_delay()
        self.write(auth_answer)


    @authenticated('*')
    def delete(self):
        """
        Logout the user.
        """
        if self.current_user:
            try:
                del GLSetting.sessions[self.current_user.id]
            except KeyError:
                raise errors.NotAuthenticated

        self.set_status(200)
        self.finish()
