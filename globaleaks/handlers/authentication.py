from functools import wraps
import time

from twisted.internet.defer improt inlineCallbacks
from storm.twisted.transtact import transact
from cyclone.utils import OD

from globaleaks.models.node import Node
from globaleaks.models.receiver import Receiver
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors
from globaleaks.config import config
from globaleaks.utils import random_string

def authenticated(usertype):
    """
    Decorator for authenticated sessions.
    If the user (could be admin/receiver/wb) is not authenticated, return
    a http 401 error.
    Otherwise, update the current session and then fire :param:`method`.
    """
    def userfilter(method):
        authenticated.method = method

    def wrapper(cls, *args, **kwargs):
        if not cls.current_user:
           raise errors.NotAuthenticated
        elif authenticated.role != cls.current_user.role:
            # XXX: eventually change this
            raise errors.NotAuthenticated
        else:
            config.sessions[cls.session_id].timestamp = time.time()
            return authenticated.method(cls, *args, **kwargs)

    authenticated.role = role
    return userfilter


class Authentication(BaseHandler):
    """
    Login page for administrator
    Extra attributes:
      session_id - current id session for the user
      get_session(username, password) - generates a new session_id
    """
    session_id = None

    def get_current_user(self, session):
        """
        Overrides cyclone's get_current_user method for self.current_user property.
        """
        return config.sessions[self.session_id].id

    def generate_session(self, identifier):
       self.session_id = random_string(16, 'a-z,A-Z,0-9')
       config.sessions[self.session_id] = OD(
               timestamp=time.time(),
               id=identifier,
               role=role,
        )

    @transact
    def login_wb(self, receipt):
        store = config.main.zstorm.get('main_store')
        node_desc = store.find(WhistleblowerTip, WhistleblowerTip.receipt == unicode(receipt)).one()
        return unicode(node_desc.receipt)

    @transact
    def login_receiver(self, username, password):
        store = config.main.zstorm.get('main_store')
        fstreceiver = store.find(Receiver).first()
        return unicode(fstreceiver.receiver_gus)

    @transact
    def login_admin(self, password):
        store = config.main.zstorm.get('main_store')
        node = store.find(Node).one()
        return node.password == password

    @inlineCallbacks
    def post(self, page):
        # XXX: input validation
        request = json_decode(self.request.body)
        for field in 'username', 'password', 'role':
             if field not in request:
                 raise errors.InvalidInputFormat(repr(field))

        username = request['username']
        password = request['password']
        role = request['role']

        if role == 'admin':
            # username is ignored
            auth = yield self.login_admin(password)
        elif role == 'wb':
            # username is ignored
            auth = yield self.login_wb(password)
        elif role == 'receiver':
            auth = yield self.login_receiver(username, password)
        else:
            raise InvalidInputFormat(role)

        if not auth:
            raise errors.InvalidAuthRequest
        else:
            return self.finish(json.dumps(dict(
               session=self.generate_session(auth, role),
            )))

    def delete(self):
        """
        Logout the user.
        """
        if self.current_user:
            del self.current_user
            del config.sessions[session_id]

        self.finish()
