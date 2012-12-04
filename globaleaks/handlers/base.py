# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from globaleaks.messages import validateMessage
from cyclone.web import RequestHandler, HTTPError
from globaleaks.utils import log

DEBUG = True

class BaseHandler(RequestHandler):
    """
    GLBackendHandler is responsible for the verification and sanitization of
    requests based on what is defined in the API specification (api.py).

    I will take care of instantiating models classes that will generate for me
    output to be sent to GLClient.

    Keep in mind the following gotchas:

    When you decorate a handler with @inlineCallbacks or are returning a
    deferred be sure to decorate it also with @asynchronous (order does not
    matter).

    Operations on objects should go inside of models, because in here it is not
    possible to instantiate a Store object without blocking.

    Messages can be validated with messages.validateMessage. This will output
    the validated message.

    An example usage:
        request = message.validateMessage(self.request.body,
                            message.requests.submissionStatus)

    Request is now a dict that I can interact with.

    """
    log.debug("[D] %s %s " % (__file__, __name__), "BaseHandler")

    requestTypes = {}
    def prepare(self):
        """
        This method is called by cyclone, and is implemented to
        handle the POST fallback, in environment where PUT and DELETE
        method may not be used.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "BaseHandler", "prepare")
        print "Just got %s" % self.request.body
        if self.request.method.lower() == 'post':
            try:
                wrappedMethod = self.get_argument('method')[0]
                print "[^] Forwarding", wrappedMethod, "from POST"
                if wrappedMethod.lower() == 'delete' or \
                        wrappedMethod.lower() == 'put':
                    self.request.method = wrappedMethod.upper()
            except HTTPError:
                pass
        if self.request.method in self.requestTypes:
            validMessage = self.requestTypes[self.request.method]
            validateMessage(self.request.body, validMessage)

