import time
from storm.exceptions import NotOneError

from twisted.internet.defer import inlineCallbacks
from cyclone.util import ObjectDict as OD

from globaleaks.models import Node
from globaleaks.settings import transact
from globaleaks.models import Receiver, WhistleblowerTip
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors, requests
from globaleaks import settings
from globaleaks.utils import random_string, log

def authenticated(*roles):
    """
    Decorator for authenticated sessions.
    If the user (could be admin/receiver/wb) is not authenticated, return
    a http 401 error.
    Otherwise, update the current session and then fire :param:`method`.
    """
    def wrapper(method):
        def call_method(cls, *args, **kwargs):
            for role in roles:
                if not cls.current_user:
                    raise errors.NotAuthenticated
                elif role != cls.current_user.role:
                    # XXX: eventually change this
                    raise errors.NotAuthenticated
                else:
                    settings.sessions[cls.current_user.id].timestamp = time.time()
            return method(cls, *args, **kwargs)
        return call_method
    return wrapper

@transact
def login_wb(store, receipt):
    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.receipt == unicode(receipt)).one()

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
        # XXX Security paranoia: insert random delay
        raise errors.InvalidAuthRequest

    if not receiver:
        log.debug("Receiver: Fail auth, userame %s do not exists" % username)
        raise errors.InvalidAuthRequest

    if receiver.password != password:
        receiver.failed_login += 1
        log.debug("Receiver: Failed auth for %s (expected %s receivedPassword %s) #%d" %\
                  (username, receiver.password, password, receiver.failed_login) )

        # this require a forced commit because otherwise the exception would cause a rollback!
        store.commit()
        raise errors.InvalidAuthRequest
    else:
        log.debug("Receiver: Good auth for %s %s" % (username, password))
        receiver.failed_login = 0
        return unicode(receiver.id)


@transact
def login_admin(store, password):
    node = store.find(Node).one()

    if node.password == password:
        log.debug("Admin: OK auth")
        return 'admin'
    else:
        log.debug("Admin: Fail auth")
        return False

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
        self.session_id = random_string(42, 'a-z,A-Z,0-9')
        # This is the format to preserve sessions in memory
        # Key = session_id, values "last access" "id" "role"
        new_session = OD(
               timestamp=time.time(),
               id=self.session_id,
               role=role,
               user_id=user_id
        )
        settings.sessions[self.session_id] = new_session
        return self.session_id


    @inlineCallbacks
    def post(self):
        """
        This is the /login handler expecting login/password/role
        """
        request = self.validate_message(self.request.body, requests.authDict)

        username = request['username']
        password = request['password']
        role = request['role']

        if role == 'admin':
            # username is ignored
            user_id = yield login_admin(password)
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
                print settings.sessions[self.current_user.id]
                del settings.sessions[self.current_user.id]
            except KeyError:
                raise errors.NotAuthenticated

        self.set_status(200)
        self.finish()

