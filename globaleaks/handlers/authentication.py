import time
from storm.exceptions import NotOneError

from twisted.internet.defer import inlineCallbacks
from cyclone.util import ObjectDict as OD

from globaleaks.models import Node
from globaleaks.settings import transact, GLSetting
from globaleaks.models import Receiver, WhistleblowerTip
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks.utils import log
from globaleaks.third_party import rstr
from globaleaks import security

def authenticated(*roles):
    """
    Decorator for authenticated sessions.
    If the user (could be admin/receiver/wb) is not authenticated, return
    a http 401 error.
    Otherwise, update the current session and then fire :param:`method`.
    """
    def wrapper(method_handler):
        def call_handler(cls, *args, **kwargs):
            for role in roles:
                if not cls.current_user:
                    raise errors.NotAuthenticated
                elif role != cls.current_user.role:
                    log.err("Authenticated with a different required user: now %s, expected %s" %
                            (cls.current_user.role, role) )
                    raise errors.NotAuthenticated
                else:
                    GLSetting.sessions[cls.current_user.id].timestamp = time.time()
            return method_handler(cls, *args, **kwargs)
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
    maybe forbidden if in Tor2Web, return 403 (Forbidden)
    """
    def wrapper(method_handler):
        def call_handler(cls, *args, **kwargs):
            """
            GLSettings contain the copy of the latest admin configuration, this
            enhance performance instead of searching in te DB at every handler
            connection.
            """
            accept_tor2web = GLSetting.tor2web_permitted_ops[wrapped_handler_role]
            are_we_tor2web = get_tor2web_header(cls.request.headers)

            if are_we_tor2web:
                log.debug("Uh! Is from T2W the request for: %s" % cls.request.uri)

            if are_we_tor2web and accept_tor2web == False:
                log.err("Receiver connection on Tor2Web for role %s: forbidden in %s" %
                    (wrapped_handler_role, cls.request.uri) )
                raise errors.TorNetworkRequired

            return method_handler(cls, *args, **kwargs)
        return call_handler
    return wrapper


@transact
def login_wb(store, receipt):
    try:
        wb_tip = store.find(WhistleblowerTip,
                            WhistleblowerTip.receipt == unicode(receipt)).one()
    except NotOneError, e:
        # This is one of the fatal error that never need to happen
        log.err("Expected unique fields (receipt) is not unique with %s" % receipt)
        raise errors.InvalidAuthRequest

    if not wb_tip:
        log.debug("Whistleblower: Fail auth (%s)" % receipt)
        raise errors.InvalidAuthRequest

    log.debug("Whistleblower: OK auth using: %s" % receipt )
    return unicode(wb_tip.id)


@transact
def login_receiver(store, username, password):
    """
    This login receiver need to collect also the amount of unsuccessful
    consecutive logins, because this element may bring to password lockdown.
    """
    try:
        receiver = store.find(Receiver, (Receiver.username == unicode(username))).one()
    except NotOneError:
        log.debug("Receiver: Fail auth, userame %s do not exists" % username)
        security.insert_random_delay()
        raise errors.InvalidAuthRequest

    if not receiver:
        log.debug("Receiver: Fail auth, userame %s do not exists" % username)
        security.insert_random_delay()
        raise errors.InvalidAuthRequest

    if not security.check_password(password, receiver.password, receiver.username):
        receiver.failed_login += 1
        log.debug("Receiver: Failed auth for %s #%d" % (username, receiver.failed_login) )

        # this require a forced commit because otherwise the exception would cause a rollback!
        store.commit()
        raise errors.InvalidAuthRequest
    else:
        log.debug("Receiver: Good auth for %s" % username)
        receiver.failed_login = 0
        return unicode(receiver.id)


@transact
def login_admin(store, password):
    node = store.find(Node).one()

    if not security.check_password(password, node.password, node.salt):
        log.debug("Admin: Fail auth")
        return False
    else:
        log.debug("Admin: OK auth")
        return 'admin'


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
               timestamp=time.time(),
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
        here is performed the validation of the transport stream, to avoid an user
        login himself using Tor2Web. This behavior actually can't happen (because there
        are not a redirect on /login if the unsafe transport is detected, but if someone
        try to access using the unsafe channel, because is writing the URL by personal choose,
        is forbidden and reported as warning.
        """
        request = self.validate_message(self.request.body, requests.authDict)

        username = request['username']
        password = request['password']
        role = request['role']

        if role == 'admin':
            # username is ignored
            user_id = yield login_admin(password)
            security_tranport_role = role
        elif role == 'wb':
            # username is ignored
            user_id = yield login_wb(password)
            security_tranport_role = 'tip'
        elif role == 'receiver':
            user_id = yield login_receiver(username, password)
            security_tranport_role = 'receiver'
        else:
            raise errors.InvalidInputFormat(role)

        if not user_id:
            raise errors.InvalidAuthRequest

        # Channel safety checks
        are_we_tor2web = get_tor2web_header(self.request.headers)
        accept_tor2web = GLSetting.tor2web_permitted_ops[security_tranport_role]
        if are_we_tor2web and accept_tor2web == False:
            log.err("Role [%s] has authentcated himself via unsafe channel (info: %s)" %
                (role, username) )
            # The error is the same of invalid L/P to avoid disclosure of valid credentials
            raise errors.InvalidAuthRequest

        self.write({'session_id': self.generate_session(role, user_id) ,
                    'user_id': unicode(user_id)})


    def delete(self):
        """
        Logout the user.
        """
        if self.current_user:
            try:
                log.debug("Explitic logout of SID %s" % GLSetting.sessions[self.current_user.id])
                del GLSetting.sessions[self.current_user.id]
            except KeyError:
                raise errors.NotAuthenticated

        self.set_status(200)
        self.finish()

