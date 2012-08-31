from twisted.internet.defer import inlineCallbacks, returnValue
from globaleaks import node
from globaleaks.tip import Tip
from globaleaks.admin import Admin
from globaleaks.receiver import Receiver
from globaleaks.submission import Submission
from globaleaks.rest.hooks.validators import *
from globaleaks.rest.hooks.sanitizers import *
from globaleaks.utils import logging

from globaleaks import DummyHandler

from cyclone import escape
from cyclone.web import RequestHandler, HTTPError, asynchronous

DEBUG = True

class GLBackendHandler(RequestHandler):
    """
    Provides common functionality for GLBackend Request handlers.
    """
    target = DummyHandler()

    # Used for passing status code from handlers to client
    status_code = None

    # The request method
    method = None

    # Arguments being sent from client via POST/GET/DELETE/PUT
    arguments = []

    keywordArguments = {}

    # Arguments matched from the in the regexp of the REST spec
    matchedArguments = []

    # The methods supported by this specific handler
    supportedMethods = None

    # The class responsible for handling sanitization
    sanitizer = None

    # The class responsible for handling validation
    validator = None

    def initialize(self, action=None, supportedMethods=None):
        """
        Get the argument passed by the API dict.

        Configure the target handler to point to the GLBackendHandler. This
        allows the globaleaks core handlers to reach the request object.

        :action the action such request is referring to.
        """
        self.action = action
        if supportedMethods:
            self.SUPPORTED_METHODS = supportedMethods
        self.target.handler = self

    def prepare(self):
        """
        If we detect that the client is using the "post hack" to send a method
        not supported by their browser, perform the "post hack".
        """
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

    def sanitizeRequest(self):
        """
        Sanitize the request. Sets the arguments array and dict to the sanized
        values.
        """
        if not self.sanitizer:
            return

        sanitize_function = lambda request: request.request.arguments
        try:
            sanitize_function = getattr(self.sanitizer, self.action)
        except:
            sanitizer_function = getattr(self.sanitizer, 'sanitize')

        # XXX should we return args and kw or only kw?
        sanitized_arguments = sanitize_function(self)

        self.arguments = sanitized_arguments

    def isSupportedMethod(self):
        """
        Check if the request method is supported.
        """
        if not self.supportedMethods:
            return True

        if self.method in self.supportedMethods:
            return True

        else:
            return False

    def validateRequest(self):
        """
        Validate the incomming request.

        Returns True if the request is valid, False if it is not.
        """
        valid = True
        if DEBUG:
            print "[+] validating %s %s via %s->%sValidate" % (self.arguments,
                                                               self.matchedArguments,
                                                                self.target,
                                                                self.action)
        if not self.validator:
            return valid

        try:
            validate_function = getattr(self.validator, self.action)
        except:
            validate_function = getattr(self.validator, 'validate')

        if validate_function:
            valid = validate_function(self)

        return valid

    @inlineCallbacks
    def handle(self, action):
        """
        Make the target handle deal with the request.
        Basically we do Target->method(*arg, **kw)

        :action the name of the method to be called on self.target
        """
        self.action = action
        return_value = {}
        validate_function = None
        processor = None

        if not action:
            returnValue(return_value)

        if DEBUG:
            print "[+] calling %s->%s with %s %s" % (self.target, self.method,
                                                     self.arguments,
                                                     self.matchedArguments)
        if not self.isSupportedMethod():
            raise HTTPError(405, "Request method not supported by this API call")

        if not self.validateRequest():
            print "[!] Detected an invalid request, are we under attack?"
            raise HTTPError(405, "Invalid request")

        self.sanitizeRequest()

        try:
            # We want to call target.action(GET|POST|DELETE|PUT)
            processor = getattr(self.target, action+self.method.upper())
        except:
            processor = getattr(self.target, action)

        return_value = yield processor(*self.matchedArguments, **self.arguments)

        returnValue(return_value)

    @asynchronous
    @inlineCallbacks
    def anyMethod(self, *arg, **kw):
        """
        Simple hack to by default handle all methods with the same handler.
        """
        if DEBUG:
            print "[+] Handling %s with %s %s" % (self.method, arg, kw)

        self.matchedArguments = arg if arg else []

        ret = yield self.handle(self.action)

        if self.status_code:
            self.set_status(self.status_code)
        self.write(dict(ret))
        self.finish()

    def get(self, *arg, **kw):
        self.method = 'GET'
        self.anyMethod(*arg, **kw)

    def post(self, *arg, **kw):
        self.method = 'POST'
        self.anyMethod(*arg, **kw)

    def put(self, *arg, **kw):
        self.method = 'PUT'
        self.anyMethod(*arg, **kw)

    def delete(self, *arg, **kw):
        self.method = 'DELETE'
        self.anyMethod(*arg, **kw)


"""
I renamed the class that was DummyHandler to Processor. Handlers now are only
what provide Request Handling capabilities. Processors are what do the actual
logic based on the data taken from the client.

It looks something like this:

API -> Handlers -> Processors -> All GL Classes

- Art.
"""
class nodeHandler(GLBackendHandler):
    """
    # Node Handler
        * /node
    """
    def get(self):
        self.method = 'GET'
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
    validator = SubmissionValidator
    sanitizer = SubmissionSanitizer

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
    validator = TipValidator
    sanitizer = TipSanitizer

class receiverHandler(GLBackendHandler):
    """
    # Receiver Handlers
        * /reciever/<ID>/
        * /receiver/<ID>/<MODULE>
    """
    target = Receiver()
    validator = ReceiverValidator
    sanitizer = ReceiverSanitizer

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
    validator = AdminValidator
    sanitizer = AdminSanitizer
