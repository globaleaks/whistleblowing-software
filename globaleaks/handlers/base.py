# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from globaleaks.messages import validateMessage
from cyclone.web import RequestHandler, HTTPError

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

    Request is now a dict that I can interacti with.

    XXX This part is not fully tested and should not be used at the moment. We
    should first get everything to work and then start doing validation, since
    the API may change and we don't want to have a layer in between us and the
    code to be tested.
    """
    requestTypes = {}
    def prepare(self):
        """
        This method is called by cyclone, and is implemented to
        handle the POST fallback, in environment where PUT and DELETE
        method may not be used.
        """
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

