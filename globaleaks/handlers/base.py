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
import collections
import json
import re

from cyclone.web import RequestHandler, HTTPError
from cyclone import escape

from globaleaks.utils import log
from globaleaks import settings
from globaleaks.rest import errors

class BaseHandler(RequestHandler):
    transactor = settings.config.main.transactor

    @property
    def store(self):
        return settings.store

    def get_store(self):
        """
        Return the current store object.
        """
        return settings.get_store()


    def validate_python_type(self, value, python_type):
        """
        Return True if the python class instantiates the python_type given.
        """
        return any((isinstance(value, python_type),
                    value is None,
        ))

    def validate_GLtype(self, value, gl_type):
        """
        Return True if the python class matches the given regexp.
        """
        return bool(re.match(gl_type, value))


    def validate_type(self, value, type):
        # if it's callable, than assumes is a primitive class
        if callable(type):
            return self.validate_python_type(value, type)
        # value as "{foo:bar}"
        elif isinstance(type, collections.Mapping):
            return self.validate_jmessage(value, type)
        # regexp
        elif isinstance(type, str):
            return self.validate_GLtype(value, type)
        # value as "[ type ]"
        elif isinstance(type, collections.Iterable):
            # empty list is ok
            if len(value) == 0:
                return True
            else:
                return all(self.validate_type(x, type[0]) for x in value)
        else:
            raise AssertionError

    def validate_jmessage(self, jmessage, message_template):
        """
        Takes a string that represents a JSON messages and checks to see if it
        conforms to the message type it is supposed to be.

        This message must be either a dict or a list. This function may be called
        recursively to validate sub-parameters that are also go GLType.

        message: the message string that should be validated

        message_type: the GLType class it should match.
        """

        if not jmessage.keys() == message_template.keys():
            log.err("Missing: %s" % (set(jmessage.keys()) - set(message_template.keys())) )
            raise errors.InvalidInputFormat('wrong schema')

        if not all(self.validate_type(jmessage[key], value) for key, value in
                    message_template.iteritems()):
            raise errors.InvalidInputFormat('wrong content')

        if not all(self.validate_type(value, message_template[key]) for key, value in
                   jmessage.iteritems()):
            raise errors.InvalidInputFormat('wrong content')

        return True

    def validate_message(self, message, message_template):
        try:
            jmessage = json.loads(message)
        except ValueError:
            raise errors.InvalidInputFormat("Invalid JSON message")

        if self.validate_jmessage(jmessage, message_template):
            return jmessage


    def output_stripping(self, message, message_template):
        """
        @param message: the serialized dict received
        @param message_template: the answers definition
        @return: a dict or a list without the unwanted keys
        """
        pass


    requestTypes = {}
    def prepare(self):
        """
        This method is called by cyclone, and is implemented to
        handle the POST fallback, in environment where PUT and DELETE
        method may not be used.
        """

        if settings.config.debug.verbose:
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
