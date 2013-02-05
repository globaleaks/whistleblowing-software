# -*- encoding: utf-8 -*-
#
#  base
#  ****
#
# Implementation of BaseHandler, the Cyclone class RequestHandler extended with our
# needings.
#
# TODO - test the prepare/POST wrapper, because has never been tested

from globaleaks.rest.base import validateMessage
from cyclone.web import RequestHandler, HTTPError
from globaleaks.config import config
import json

class BaseHandler(RequestHandler):

    requestTypes = {}
    def prepare(self):
        """
        This method is called by cyclone, and is implemented to
        handle the POST fallback, in environment where PUT and DELETE
        method may not be used.
        """

        if config.debug.verbose:
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

    def json_write(self, output):
        """
        Cyclone do not serialize in json correctly the list, only the dict.
        Then with this function we're able to serialize every content
        """

        self.set_header('Content-Type', 'application/json')

        json_data = json.dumps(output)
        self.write(json_data)
