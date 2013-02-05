# -*- encoding: utf-8 -*-
#
#  base
#  ****
#
# Implementation of BaseHandler, the Cyclone class RequestHandler extended with our
# needings.
#
# TODO - test the prepare/POST wrapper, because has never been tested

import types

from globaleaks.rest.base import validateMessage
from cyclone.web import RequestHandler, HTTPError
from cyclone import escape
from globaleaks.utils import log
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

    def write_error(self, error, **kw):
        if hasattr(error, 'http_status'):
            self.set_status(error.http_status)
            self.write({'error_message': error.error_message,
                'error_code' : error.error_code})
        else:
            RequestHandler.write_error(self, error, **kw)

    def write(self, chunk):
        """
        This is a monkey patch to RequestHandler to allow us to serialize also
        json list objects.
        """
        if isinstance(chunk, types.ListType):
            chunk = escape.json_encode(chunk)
            RequestHandler.write(self, chunk)
            self.set_header("Content-Type", "application/json")
        else:
            RequestHandler.write(self, chunk)


