from functools import wraps
import json
import time
from storm.exceptions import NotOneError

from twisted.internet.defer import inlineCallbacks
from cyclone.util import ObjectDict as OD

from globaleaks.models import Node
from globaleaks.settings import transact
from globaleaks.models import Receiver
from globaleaks.models import WhistleblowerTip
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest.errors import InvalidAuthRequest, InvalidInputFormat, NotAuthenticated
from globaleaks import settings
from globaleaks.utils.random import random_string

def authenticated(role):
    """
    Decorator for authenticated sessions.
    If the user (could be admin/receiver/wb) is not authenticated, return
    a http 401 error.
    Otherwise, update the current session and then fire :param:`method`.
    """
    def wrapper(method):
        def call_method(cls, *args, **kwargs):
            if not cls.current_user:
                raise NotAuthenticated
            elif role != cls.current_user.role:
                # XXX: eventually change this
                raise NotAuthenticated
            else:
                settings.sessions[cls.current_user.id].timestamp = time.time()
            return method(cls, *args, **kwargs)
        return call_method
    return wrapper

class AuthenticationHandler(BaseHandler):
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
        return settings.sessions[self.session_id]

    def generate_session(self, role):
        self.session_id = random_string(42, 'a-z,A-Z,0-9')
        # This is the format to preserve sessions in memory
        # Key = session_id, values "last access" "id" "role"
        new_session = OD(
               timestamp=time.time(),
               id=self.session_id,
               role=role,
        )
        settings.sessions[self.session_id] = new_session
        return self.session_id

    @transact
    def login_wb(self, store, receipt):
        try:
            wb = store.find(WhistleblowerTip,
                            WhistleblowerTip.receipt == unicode(receipt)).one()
        except NotOneError:
            raise InvalidAuthRequest

        if not wb:
            raise InvalidAuthRequest

        return unicode(wb.receipt)

    @transact
    def login_receiver(self, store, username, password):
        try:
            fstreceiver = store.find(Receiver, (Receiver.username == unicode(username), Receiver.password == unicode(password))).one()
        except NotOneError:
            raise InvalidAuthRequest
        if not fstreceiver:
            raise InvalidAuthRequest

        return unicode(fstreceiver.receiver_gus)

    @transact
    def login_admin(self, store, password):
        node = store.find(Node).one()
        return node.password == password

    @inlineCallbacks
    def post(self):
        try:
            request = json.loads(self.request.body)
            # TODO modify with the validateMessage
            if not all((field in request) for field in  ('username', 'password', 'role')):
                 raise ValueError
        except ValueError, e:
            raise InvalidInputFormat('invalid json')

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
            raise InvalidAuthRequest

        self.write({'session_id': self.generate_session(role)})

    def delete(self):
        """
        Logout the user.
        """
        if self.current_user:
            try:
                del settings.sessions[self.current_user.id]
            except KeyError:
                raise NotAuthenticated

        self.finish()
