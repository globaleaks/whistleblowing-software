# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from cyclone.web import RequestHandler

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

