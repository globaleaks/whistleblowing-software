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
from globaleaks.utils import random_string

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

    @transact
    def login_wb(self, store, receipt):
        try:
            wb_tip = store.find(WhistleblowerTip,
                                WhistleblowerTip.receipt == unicode(receipt)).one()
        except NotOneError:
            raise InvalidAuthRequest

        if not wb_tip:
            raise InvalidAuthRequest
        
        return unicode(wb_tip.id)

    @transact
    def login_receiver(self, store, username, password):
        try:
            receiver = store.find(Receiver, (Receiver.username == unicode(username), Receiver.password == unicode(password))).one()
        except NotOneError:
            raise InvalidAuthRequest
        if not receiver:
            raise InvalidAuthRequest

        return unicode(receiver.id)

    @transact
    def login_admin(self, store, password):
        node = store.find(Node).one()
        if node.password == password:
            return 'admin'
        else:
            return False

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
            user_id = yield self.login_admin(password)
        elif role == 'wb':
            # username is ignored
            user_id = yield self.login_wb(password)
        elif role == 'receiver':
            user_id = yield self.login_receiver(username, password)
        else:
            raise InvalidInputFormat(role)

        if not user_id:
            raise InvalidAuthRequest

        self.write({'session_id': self.generate_session(role, user_id)})

    def delete(self):
        """
        Logout the user.
        """
        if self.current_user:
            try:
                print settings.sessions[self.current_user.id]
                del settings.sessions[self.current_user.id]
            except KeyError:
                raise NotAuthenticated

        self.set_status(200)
        self.finish()

