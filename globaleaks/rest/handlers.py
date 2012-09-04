from twisted.internet.defer import inlineCallbacks, returnValue
from globaleaks import node
from globaleaks.tip import Tip
from globaleaks.admin import Admin
from globaleaks.receiver import Receiver
from globaleaks.submission import Submission
from globaleaks.rest.hooks.validators import *
from globaleaks.rest.hooks.sanitizers import *

from globaleaks import DummyHandler
from globaleaks.utils.JSONhelper import genericDict

from cyclone import escape
from cyclone.web import RequestHandler, HTTPError, asynchronous

DEBUG = True

class GLBackendHandler(RequestHandler):
    """
    GLBackendHandler is responsible for the verification and sanitization of
    requests based on what is defined in the API specification (api.py).

    It will do all the top level wiring to make sure that what is being
    requested from the user is handled by the respectivee processor class.

    The processor classes are:
        * Node
        * Submission
        * Tip
        * Admin
        * Receiver

    These are found in globaleaks/.

    The hooks for sanitization and verification of user supplied data is found
    inside of globaleaks/rest/hooks/.
    """

    # Used for passing status code from handlers to client
    status_code = None
    method = None

    # Arguments matched from the in the regexp of the REST spec
    matchedArguments = []
    # Store the sanitized request
    requestDict = None

    supportedMethods = None

    # Validation and sanitization classes
    sanitizer = None
    validator = None

    # The target class that will be responsible for handling the request
    processor = None

    def initialize(self, action=None, supportedMethods=None):
        """
        Get the argument passed by the API dict.

        Configure the processor handler to point to the GLBackendHandler. This
        allows the globaleaks core handlers to reach the request object.

        :action the action such request is referring to.
        """
        self.action = action
        if supportedMethods:
            self.SUPPORTED_METHODS = supportedMethods

        if self.processor:
            self.processor.handler = self

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

        # We first try and call the method named after action.
        # If that method does not exist we fail over to calling the "sanitize"
        # method.
        # If no method named "sanitize" exists in the sanitizer function, we
        # will throw an error.
        try:
            sanitize_function = getattr(self.sanitizer, self.action)
        except:
            sanitizer_function = getattr(self.sanitizer, 'sanitize')

        # XXX should we return args and kw or only kw?
        sanitized_request = sanitize_function(self.request)

        self.requestDict = sanitized_request

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
                                                                self.processor,
                                                                self.action)
        if not self.validator:
            return valid

        try:
            validate_function = getattr(self.validator, self.action)
        except:
            validate_function = getattr(self.validator, 'validate')

        if validate_function:
            valid = validate_function(self.request)

        return valid

    @inlineCallbacks
    def handle(self, action):
        """
        Make the processor handle deal with the request.
        Basically we do Processor->method(*arg, **kw)

        :action the name of the method to be called on self.processor
        """
        self.action = action
        return_value = {}
        validate_function = None
        processor = None

        if not action:
            returnValue(return_value)

        if DEBUG:
            print "[+] calling %s->%s with %s %s" % (self.processor, self.method,
                                                     self.arguments,
                                                     self.matchedArguments)
        if not self.isSupportedMethod():
            raise HTTPError(405, "Request method not supported by this API call")

        if not self.validateRequest():
            print "[!] Detected an invalid request, are we under attack?"
            raise HTTPError(405, "Invalid request")

        self.sanitizeRequest()

        try:
            # We want to call processor.action(GET|POST|DELETE|PUT)
            processor = getattr(self.processor, action+self.method.upper())
        except:
            processor = getattr(self.processor, action)

        return_value = yield processor(*self.matchedArguments,
                **self.requestDict)

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
XXX
please, clarify if the handlers extend GLBackendHandler or DummyHandler
                if the handlers are implemented here or in ../$namestuff.py
---
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
    processor = Submission()
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
    processor = Tip()
    validator = TipValidator
    sanitizer = TipSanitizer

class receiverHandler(GLBackendHandler):
    """
    # Receiver Handlers
        * /reciever/<ID>/
        * /receiver/<ID>/<MODULE>
    """
    processor = Receiver()
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
    processor = Admin()
    validator = AdminValidator
    sanitizer = AdminSanitizer
