import time
from storm.exceptions import NotOneError

from twisted.internet.defer import inlineCallbacks
from cyclone.util import ObjectDict as OD

from globaleaks.models import Node, User
from globaleaks.settings import transact, GLSetting
from globaleaks.models import Receiver, WhistleblowerTip
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks.utils import log
from globaleaks.third_party import rstr
from globaleaks import security, utils

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

            if role == cls.current_user.role:

                session_info = GLSetting.sessions[cls.current_user.id]

                if utils.is_expired(session_info.borndate,
                    seconds=GLSetting.defaults.lifetimes[cls.current_user.role]):

                    copy_role = cls.current_user.role
                    copy_lifetime = GLSetting.defaults.lifetimes[cls.current_user.role]
                    del GLSetting.sessions[cls.current_user.id]

                    log.debug("Authentication Expired (%s) %s seconds" % (copy_role, copy_lifetime))
                    raise errors.SessionExpired(copy_lifetime, copy_role)

                log.debug("Authentication OK (%s)" % role )
                # update the access time to the latest
                GLSetting.sessions[cls.current_user.id].borndate = utils.datetime_now()
                return method_handler(cls, *args, **kwargs)

            # else, if role != cls.current_user.role
            log.err("Authenticated with a different required user: now %s, expected %s" %
                    (cls.current_user.role, role) )
            raise errors.InvalidScopeAuth("Good login in wrong scope: you %s, expected %s" %
                                          (cls.current_user.role, role) )

        return call_handler
    return wrapper


def get_tor2web_header(request_headers):
    """
    @param request_headers: HTTP headers
    @return: True or False
    content string of X-Tor2Web header is ignored
    """
    key_content = request_headers.get('X-Tor2Web', None)
    return True if key_content else False

def transport_security_check(wrapped_handler_role):
    """
    Decorator for enforce a minimum security on the transport mode.
    Tor and Tor2Web has two different protection level, and some operation
    maybe forbidden if in Tor2Web, return 417 (Expectation Fail)
    """
    tor2web_roles = ['tip', 'submission', 'receiver', 'admin', 'unauth']

    def wrapper(method_handler):
        def call_handler(cls, *args, **kwargs):
            """
            GLSetting contain the copy of the latest admin configuration, this
            enhance performance instead of searching in te DB at every handler
            connection.
            """
            assert wrapped_handler_role in tor2web_roles
            if wrapped_handler_role == 'tip':
                accept_tor2web = GLSetting.memory_copy.tor2web_tip
            elif wrapped_handler_role == 'submission':
                accept_tor2web = GLSetting.memory_copy.tor2web_submission
            elif wrapped_handler_role == 'receiver':
                accept_tor2web = GLSetting.memory_copy.tor2web_receiver
            elif wrapped_handler_role == 'admin':
                accept_tor2web = GLSetting.memory_copy.tor2web_admin
            else:
                accept_tor2web = GLSetting.memory_copy.tor2web_unauth

            are_we_tor2web = get_tor2web_header(cls.request.headers)

            if are_we_tor2web and accept_tor2web == False:
                log.err("Receiver connection on Tor2Web for role %s: forbidden in %s" %
                    (wrapped_handler_role, cls.request.uri) )
                raise errors.TorNetworkRequired

            if are_we_tor2web:
                log.debug("Accepted Tor2Web connection for role '%s' in uri %s" %
                    (wrapped_handler_role, cls.request.uri) )

            return method_handler(cls, *args, **kwargs)

        return call_handler
    return wrapper


@transact
def login_wb(store, receipt):
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
    wb_tip.last_access = utils.datetime_now()
    return unicode(wb_tip.id)


@transact
def login_receiver(store, username, password):
    """
    This login receiver need to collect also the amount of unsuccessful
    consecutive logins, because this element may bring to password lockdown.
    """
    accept_credential = False

    receiver_user = store.find(User, User.username == username).one()

    if not receiver_user or receiver_user.role != 'receiver':
        log.debug("Receiver: Fail auth, username %s do not exists" % username)
        return False

    receiver = store.find(Receiver, (Receiver.user_id == receiver_user.id)).one()

    if not security.check_password(password, receiver_user.password, receiver_user.salt):
        receiver_user.failed_login_count += 1
        if receiver_user.failed_login_count == 1:
            receiver_user.fist_failed = utils.datetime_now()
    else:
        accept_credential = True
        log.debug("Receiver: Authorized receiver %s" % username)
        receiver_user.failed_login_count = 0
        receiver_user.last_login = utils.datetime_now()
        receiver_user.first_failed = utils.datetime_null()

    if receiver_user.failed_login_count >= GLSetting.failed_login_alarm:
        log.err("Warning: Receiver %s has failed %d times the password" %\
                (username, receiver_user.failed_login_count) )
        # TODO we've to trigger lockout
        # https://github.com/globaleaks/GlobaLeaks/issues/48

    if accept_credential:
        return unicode(receiver.id)
    else:
        return False


@transact
def login_admin(store, username, password):
    admin = store.find(User, (User.username == unicode(username))).one()

    admin_user = store.find(User, User.username == username).one()

    if not admin_user or admin_user.role != 'admin':
        log.debug("Receiver: Fail auth, username %s do not exists" % username)
        return False

    if not security.check_password(password, admin.password, admin.salt):
        log.debug("Admin login: Invalid password")
        admin.failed_login_count += 1
        if admin.failed_login_count == 1:
            admin_user.first_failed = utils.datetime_now()
        return False
    else:
        log.debug("Receiver: Authorized receiver %s" % username)
        admin_user.failed_login_count = 0
        admin_user.last_login = utils.datetime_now()
        admin_user.first_failed = utils.datetime_null()
        return username

class AuthenticationHandler(BaseHandler):
    """
    Login page for administrator
    Extra attributes:
      session_id - current id session for the user
      get_session(username, password) - generates a new session_id
    """
    session_id = None

    def generate_session(self, role, user_id):
        """
        Args:
            role: can be either 'admin', 'wb' or 'receiver'

            user_id: will be in the case of the receiver the receiver.id in the
                case of an admin it will be set to 'admin', in the case of the
                'wb' it will be the whistleblower id.
        """
        self.session_id = rstr.xeger(r'[A-Za-z0-9]{42}')

        # This is the format to preserve sessions in memory
        # Key = session_id, values "last access" "id" "role"
        new_session = OD(
               borndate=utils.datetime_now(),
               id=self.session_id,
               role=role,
               user_id=user_id
        )
        GLSetting.sessions[self.session_id] = new_session
        return self.session_id


    @inlineCallbacks
    def post(self):
        """
        This is the /login handler expecting login/password/role,
        """
        request = self.validate_message(self.request.body, requests.authDict)

        username = request['username']
        password = request['password']
        role = request['role']

        # Then verify credential, if the channel shall be trusted
        if role == 'admin':
            # username is ignored
            user_id = yield login_admin(username, password)
        elif role == 'wb':
            # username is ignored
            user_id = yield login_wb(password)
        elif role == 'receiver':
            user_id = yield login_receiver(username, password)
        else:
            raise errors.InvalidInputFormat(role)

        if not user_id:
            raise errors.InvalidAuthRequest

        self.write({'session_id': self.generate_session(role, user_id) ,
                    'user_id': unicode(user_id)})


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

