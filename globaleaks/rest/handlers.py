from twisted.internet.defer import inlineCallbacks, returnValue
from globaleaks import node
from globaleaks.tip import Tip
from globaleaks.node import Node
from globaleaks.admin import Admin
from globaleaks.receiver import Receiver
from globaleaks.submission import Submission
from globaleaks.rest.hooks.validators import *
from globaleaks.rest.hooks.sanitizers import *

from cyclone import escape
from cyclone.web import RequestHandler, HTTPError, asynchronous

"""
https://en.wikipedia.org/wiki/Http_error_code

The error code actually used in this file are:
    404 (Not found: handled by Cyclone)
    405 (Method not allowed)
    503 (Service not available)
"""

# decorator @removeslash in cyclone.web may remove final '/' if not
# expected. would be nice use it, but the Cyclone code check only HEAD and GET
# while we need checks in a complete CURD
# -- may this be a request to be opened in Cyclone ?

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
    # Store the sanitized request in a dict (*arg, **kw)
    safeRequest = {}

    # Validation and sanitization classes
    sanitizer = None
    validator = None

    # The target class that will be responsible for handling the request
    processor = None

    def initialize(self, action, supportedMethods):
        """
        Get the argument passed by the API dict.

        Configure the processor handler to point to the GLBackendHandler. This
        allows the globaleaks core handlers to reach the request object.

        :action is the arbitrary name used in Processor classed for
         address a method+HTTP method, its required in api.spec
        """

        self.action = action
        self.SUPPORTED_METHODS = supportedMethods

        if self.processor:
            self.processor.handler = self
        else:
            print "[!] processor not intialized, you'd make a mistake"

    def prepare(self):
        """
        This method is called by cyclone, and is implemented to
        handle the POST fallback, in environment where PUT and DELETE
        method may not be used.
        """

        if self.request.method.lower() == 'post':
            try:
                wrappedMethod = self.get_argument('method')
                print "[^] Forwarding", wrappedMethod, "from POST"
                if wrappedMethod.lower() == 'delete' or \
                        wrappedMethod.lower() == 'put':
                    self.request.method = wrappedMethod.upper()
            except HTTPError:
                pass

    def isSupportedMethod(self):
        """
        Check if the request method is supported.
        """
        return (self.method in self.SUPPORTED_METHODS)

    def validateRequest(self):
        """
        Validate the incomming request.
        Returns True if the request is valid, False if it is not.
        Validate perform logical checks and logging
        ALL the HTTP calls need to pass thru Validator
        """
        isValid = True
        validator_function = None

        if DEBUG:
            import urllib
            print "[+] validating %s %s via %s->%sValidate" %  (
                                        urllib.unquote_plus(str(self.request)),
                                        self.matchedArguments, self.processor,
                                        self.action)

        if not self.validator:
            raise HTTPError(503, "Missing of Validator Class/Method")

        for x in [ self.action + '_' + self.method, self.action, 'default' ]:
            try:
                validator_function = getattr(self.validator, x)
                break
            except:
                pass

        """
        self.request is an object: cyclone.httpserver.HTTPRequest, the important
        object values in our analysis are:
        matchedArguments (by cyclone API)
        body
        (in the future, perhaps) header
        """
        if validator_function:
            isValid = validator_function(self.request.body,
                    *self.matchedArguments)
        else:
            raise HTTPError(503, "Missing of validator function")

        return isValid

    def sanitizeRequest(self):
        """
        Sanitize the request. Sets the arguments array and dict to the sanized
        values.
        """
        # this may happen in the GET request, would not be accepted in other method
        if not self.sanitizer:
            if self.method.upper() == 'GET':
                return
            else:
                raise HTTPError(503, "Missing of Sanitizer Class/Method")

        # We first try and call the method named after action + HTTP METHOD,
        # If that method does not exist we fail over to calling the action,
        # If that method does not exist we fail over to calling the
        # "default_sanitize" method.
        # If no getattr return a method, we will throw an error.
        sanitizer_function = None

        for x in [ self.action + '_' + self.method, self.action, 'default' ]:
            try:
                sanitizer_function = getattr(self.sanitizer, x)
                break
            except:
                pass

        if sanitizer_function:
            self.safeRequest = sanitizer_function(self.request.body,
                *self.matchedArguments)
            # remind that you want to do:
            # self.request = None
        else:
            raise HTTPError(503, "Missing of sanitizer function")

        """
        return having self.safeRequest available.
        TODO, need to be a GLType returned in the action + method handler ?
        """

    @inlineCallbacks
    def handle(self, action):
        """
        Make the processor handle deal with the request.
        Basically we do Processor->reqApi(*arg, **kw)

        :action the string defined in api.spec, and would
         compose with $action_$httpmethod the method inside
         of the appropriate Process class
        """
        return_value = {}

        if DEBUG:
            import urllib
            print "[+] calling %s->%s with %s [=] %s MA/ %s" % (self.processor, self.method,
                                                     urllib.unquote_plus(str(self.request)),
                                                     self.action,
                                                     self.matchedArguments)

        if not self.isSupportedMethod():
            raise HTTPError(405, "Request method not supported by this API call")

        self.validateRequest()
        self.sanitizeRequest()

        # after this point, self.request would NOT BE USED, use instead
        # ____ self.safeRequest ____

        if self.matchedArguments:
            matchedArguments = self.matchedArguments
        else:
            matchedArguments = []
        targetMethod = getattr(self.processor, self.action + '_' + self.method.upper())
        return_value = yield targetMethod(self.safeRequest, *matchedArguments)

        if DEBUG:
            import urllib
            print "[?] handled %s->%s_%s with %s retval %s " % (
                                                     self.processor, self.action,
                                                     self.method, self.matchedArguments,
                                                     urllib.unquote_plus(str(return_value)))

        returnValue(return_value)

    @asynchronous
    @inlineCallbacks
    def anyMethod(self, *arg, **kw):
        """
        Simple hack to by default handle all methods with the same handler:
        """
        if DEBUG:
            print "[+] anyMethod -- Handling %s %s with %s %s + %s" % (self.action, \
                    self.method, arg, kw, self.matchedArguments)

        self.matchedArguments = arg if arg else []

        ret = yield self.handle(self.action)

        if self.status_code:
            self.set_status(self.status_code)

        if not ret:
            print "There is not return value !?"
            ret = ({'error': 'no return value available'})

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
Follow the GLBackend handlers, extending GLBackendHandlers
"""
class nodeHandler(GLBackendHandler):
    """
    # Node Handler (U1, GET)
        * /node

    This class has not a sanitized because
    is only a GET request, anyway has a validator
    because some logging functionality may be
    implemented in *Validator classess
    """
    processor = Node()
    validator = NodeValidator


class submissionHandler(GLBackendHandler):
    """
    # Submission Handlers (U2, U3, U4: POST GET)
                          (U5: CURD, file upload):
        * /submission/<ID>
        * /submission/<ID>/status
        * /submission/<ID>/finalize
        * /submission/<ID>/files
    """
    processor = Submission()
    validator = SubmissionValidator
    sanitizer = SubmissionSanitizer


class tipHandler(GLBackendHandler):
    """
    # Tip Handlers
        * /tip/<ID>            T1 GET POST (all)
        * /tip/<ID>/comment    T2 POST (wb/rcv)
        * /tip/<ID>/files      T3 CURD (wb)
        * /tip/<ID>/finalize   T4 post (wb)
        * /tip/<ID>/download   T5 GET (rcv)
        * /tip/<ID>/pertinence T6 POST (rcv)
    """
    processor = Tip()
    validator = TipValidator
    sanitizer = TipSanitizer

class receiverHandler(GLBackendHandler):
    """
    # Receiver Handlers (R1 GET, R2 CURD)
        * /reciever/<TID>
        * /receiver/<MODULE_TYPE><fixd><TID>/module
    """
    processor = Receiver()
    validator = ReceiverValidator
    sanitizer = ReceiverSanitizer

class adminHandler(GLBackendHandler):
    """
    # Admin Handlers (A1 GET POST, A2 A3 A4 CURD)
        * /admin/node
        * /admin/contexts
        * /admin/receivers/<context_ID>
        * /admin/modules/<MODULE_TYPE><fixd><context_ID>
    """
    processor = Admin()
    validator = AdminValidator
    sanitizer = AdminSanitizer
