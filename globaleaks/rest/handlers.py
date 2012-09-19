"""
https://en.wikipedia.org/wiki/Http_error_code
"""

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

# decorator @removeslash in cyclone.web may remove final '/' if not 
# expected. would be nice use it, but the Cyclone code check only HEAD and GET
# while we need checks in a complete CURD

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
    safeRequest = None

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
        else:
            print "[!] processor not intialized, you'd make a mistake"

    def prepare(self):
        """
        If we detect that the client is using the "post hack" to send a method
        not supported by their browser, perform the "post hack".
        """

        if self.request.method.lower() is 'post':
            wrappedMethod = None

            try:
                if self.get_argument('put'):
                    print "I've PUT"
                    wrappedMethod = 'put'

                if self.get_argument('delete'):
                    print "I've DELETE"
                    # if both are present, its an error
                    if wrappedMethod:
                        print "[!] Conflict in PUT|DELETE wrapper"
                        raise HTTPError(409) # Conflict

                    wrappedMethod = 'delete'

                if wrappedMethod:
                    print "[^] Forwarding", wrappedMethod, "from POST"
                    self.post_hack(wrappedMethod)

            except HTTPError:
                pass


    def post_hack(self, method):
        """
        This serves to map a POST with argument method set to one of the
        allowed methods (DELETE, PUT) to that method call.

        The POST format has been checked before, the wrapping 
        flags are removed, and the PUT|DELETE are treated like every
        other CURD operation
        """

        print self.request
        self.request = 'fuffa'
        print self.request

        if method in self.SUPPORTED_METHODS:
            self.request.method = method
        else:
            raise HTTPError(405) # method not allowed

    def sanitizeRequest(self):
        """
        Sanitize the request. Sets the arguments array and dict to the sanized
        values.
        """
        print self.__class__, "sanitizer", self.sanitizer, "action", self.action

        if not self.sanitizer:
            return

        # We first try and call the method named after action.
        # If that method does not exist we fail over to calling the "sanitize"
        # method.
        # If no method named "sanitize" exists in the sanitizer function, we
        # will throw an error.
        try:
            sanitizer_function = getattr(self.sanitizer, self.action)
        except:
            sanitizer_function = getattr(self.sanitizer, 'sanitize')

        self.safeRequest = sanitizer_function(self.request)

    def isSupportedMethod(self):
        """
        Check if the request method is supported.
        """

        # having not configured supportedMethods mean TRUE in all methods ? XXX
        if not self.supportedMethods:
            print "Hell yes! self.supportedMethods = NONE"
            return True
        else:
            print "Hell NO ! self.supportedMethods = some", str(self.supportedMethods)


        if self.method in self.supportedMethods:
            return True
        else:
            return False

    def validateRequest(self):
        """
        Validate the incomming request.
        Returns True if the request is valid, False if it is not.
        Validate perform logical checks and logging
        """
        isValid = True
        if DEBUG:
            import urllib
            print "[+] validating %s %s via %s->%sValidate" %  (
                                        urllib.unquote_plus(str(self.request)),
                                        self.matchedArguments, self.processor, 
                                        self.action)

        if not self.validator:
            return isValid

        try:
            validate_function = getattr(self.validator, self.action)
        except:
            validate_function = getattr(self.validator, 'validate')

        if validate_function:
            isalid = validate_function(self.request)

        return isValid

    @inlineCallbacks
    def handle(self, reqMethod):
        """
        Make the processor handle deal with the request.
        Basically we do Processor->method(*arg, **kw)

        :reqMethod is the method to be called on self.processor
        """
        print self.__class__, "handle action:", reqMethod

        return_value = {}
        validate_function = None
        processor = None

        if not reqMethod:
            returnValue(return_value)

        self.action = reqMethod

        if DEBUG:
            print type(self.request)
            import urllib
            print "[+] calling %s->%s with %s [=] %s %s" % (self.processor, self.method,
                                                     urllib.unquote_plus(str(self.request)),
                                                     self.action,
                                                     self.matchedArguments)
        if not self.isSupportedMethod():
            raise HTTPError(405, "Request method not supported by this API call")

        if not self.validateRequest():
            print "[!] Detected malformed request: are we under attack?"
            raise HTTPError(405, "Invalid request")

        self.sanitizeRequest()
        # after this point, self.request would NOT BE USED, use instead
        # self.safeRequest

        try:
            # We aim to processor.$action => processor.[GET|POST|DELETE|PUT]
            targetMethod = getattr(self.processor, self.action+self.method.upper())
            print "1) found method using the sum:", action+self.method.upper()
        except:
            targetMethod = getattr(self.processor, self.action)
            print "2) found method using just:", self.action

# return_value = yield targetMethod(*self.matchedArguments, **self.safeRequest)
# cause:
# exceptions.TypeError: context() argument after ** must be a mapping, not HTTPRequest
        return_value = targetMethod(self)

        if DEBUG:
            print "[?] handled %s->%s with %s %s retval %s" % (
                                                     self.processor, self.method,
                                                     self.action,
                                                     self.matchedArguments, return_value)
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

    def get(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.method = 'GET'
        self.write(dict(node.info))

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

    def get(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})

    def post(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})


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

    def get(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})

    def post(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})


class receiverHandler(GLBackendHandler):
    """
    # Receiver Handlers (R1 GET, R2 CURD)
        * /reciever/<ID>
        * /receiver/<ID>/<MODULE_TYPE>
    """
    processor = Receiver()
    validator = ReceiverValidator
    sanitizer = ReceiverSanitizer

    def get(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})

    def post(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})

class adminHandler(GLBackendHandler):
    """
    # Admin Handlers (A1 GET POST, A2 A3 A4 CURD)
        * /admin/node  
        * /admin/contexts
        * /admin/receivers/<context_ID>
        * /admin/modules/<MODULE_TYPE>
    """
    processor = Admin()
    validator = AdminValidator
    sanitizer = AdminSanitizer

    def get(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})

    def post(self, *arg, **kw):
        print self.__class__,__name__ , arg, kw
        self.write({'answer': 'something'})

