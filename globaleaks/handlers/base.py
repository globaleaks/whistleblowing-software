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


    # validate_type = isinstance    # eventually later
    def validate_python_type(self, value, python_type):
        """
        Return True if the python class instantiates the python_type given.
        """
        return any((isinstance(value, python_type),
                    not value,
        ))

    def validate_GLtype(self, value, gl_type):
        """
        Return True if the python class matches the given regexp.
        """
        print gl_type
        return bool(re.match(value, gl_type))


    def validate_type(self, value, type):
        # if it's callable, than assumes is a primitive class
        if callable(type):
            return self.validate_python_type(value, type)
        # value as "{foo:bar}"
        elif isinstance(type, collections.Mapping):
            self.validate_jmessage(value, type)
        # value as "[ type ]"
        elif isinstance(type, collections.Iterable):
            # empty list is ok
            if len(value) == 0:
                return True
            else:
                return all(self.validate_type(x, type[0]) for x in value)
        # regexp
        else:
            self.validate_GLtype(value, type)

    def validate_jmessage(self, jmessage, message_template):
        """
        Takes a string that represents a JSON messages and checks to see if it
        conforms to the message type it is supposed to be.

        This message must be either a dict or a list. This function may be called
        recursively to validate sub-parameters that are also go GLType.

        message: the message string that should be validated

        message_type: the GLType class it should match.
        """

        # fuck funky differences between client and server
        # if not jmessage.keys() == message_template.keys():
        #     print sorted(jmessage.keys()), sorted(message_template.keys())
        #     raise errors.InvalidInputFormat('wrong schema')

        # if not all(self.validate_type(jmessage[key], value) for key, value in
        #            message_template.iteritems()):
        #     print jmessage, message_template
        #     raise errors.InvalidInputFormat('wrong content')

        # XXX the schema followed is passed by the user, in the future we need
        # that specification is used as reference schema. In develop this has raised
        # bugs/issue/incompatibility

        if not all(self.validate_type(value, message_template[key]) for key, value in
                   jmessage.iteritems()):
            # print "+ Template", sorted(message_template.keys())
            # print "- Received", sorted(jmessage.iteritems())
            # print "** diff", set(message_template.keys()) - set(jmessage.keys())
            raise errors.InvalidInputFormat('wrong content')

        return True

    def validate_message(self, message, message_template):
        try:
            jmessage = json.loads(message)
        except ValueError:
            raise errors.InvalidInputFormat("Invalid JSON message")

        # Disabled Input Validation - until specification is not complete
        return jmessage

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
