"""
    handlers
    ********

    This contains all of the handlers for the REST interface.
    Should not contain any logic that is specific to the operations to be done
    by the particular REST interface.
"""

from globaleaks import node
from globaleaks.tip import Tip
from globaleaks.admin import Admin
from globaleaks.receiver import Receiver
from globaleaks.submission import Submission

from globaleaks import DummyHandler
from globaleaks.utils.JSONhelper import genericDict

from cyclone import escape
from cyclone.web import RequestHandler

class GLBackendHandler(RequestHandler):
    """
    Provides common functionality for GLBackend Request handlers.
    """
    target = DummyHandler()

    def initialize(self, action=None):
        self.action = action
        self.target.handler = self
        print self.request

    def prepare(self):
        if self.request.method.lower() is 'post' and \
                self.get_argument('method'):
            self.post_hack(self.get_argument('method'))

    def post_hack(self, method):
        """
        This serves to map a POST with argument method set to one of the
        allowed methods (DELETE, PUT) to that method call.
        """
        if method in self.SUPPORTED_METHODS:
            self.request.method = method
        else:
            raise HTTPError(405)

    def handle(self, method, *arg, **kw):
        ret = {}
        if method:
            func = getattr(self.target, method)
            ret = func(*arg, **kw)
        return ret

    def any_method(self, method, *arg, **kw):
        ret = self.handle(self.action, *arg, **kw)
        self.write(dict(ret))

    def get(self, *arg, **kw):
        self.any_method('get', *arg, **kw)

    def post(self, *arg, **kw):
        self.any_method('post', *arg, **kw)

    def put(self, *arg, **kw):
        self.any_method('put', *arg, **kw)

    def delete(self, *arg, **kw):
        self.any_method('delete', *arg, **kw)

class nodeHandler(GLBackendHandler):
    """
    # Node Handler
        * /node
    """
    def get(self):
        self.write(dict(node.info))

class submissionHandler(GLBackendHandler):
    """
    # Submission Handlers
        * /submission/<ID>/
        * /submission/<ID>/fields
        * /submission/<ID>/groups
        * /submission/<ID>/files
        * /submission/<ID>/finalize
    """
    target = Submission()

class tipHandler(GLBackendHandler):
    """
    # Tip Handlers
        * /tip/<ID>/
        * /tip/<ID>/comment
        * /tip/<ID>/files
        * /tip/<ID>/finalize
        * /tip/<ID>/download
        * /tip/<ID>/pertinence
    """
    target = Tip()

class receiverHandler(GLBackendHandler):
    """
    # Receiver Handlers
        * /reciever/<ID>/
        * /receiver/<ID>/<MODULE>
    """
    target = Receiver()

class adminHandler(GLBackendHandler):
    """
    # Admin Handlers
        * /admin/node
        * /admin/contexts
        * /admin/groups/<ID>
        * /admin/receivers/<ID>
        * /admin/modules/<MODULE>
    """
    target = Admin()

