# -*- encoding: utf-8 -*-
#
#  base
#  ****
#
# Implementation of BaseHandler, the Cyclone class RequestHandler extended with our
# needings.
#
# TODO - test the prepare/POST wrapper, because has never been tested

import httplib
import types
import collections
import json
import re
import sys

from cyclone.web import RequestHandler, HTTPError, HTTPAuthenticationRequired
from cyclone import escape

from globaleaks.utils import log, MailException
from globaleaks import settings
from globaleaks.rest import errors

class BaseHandler(RequestHandler):

    @staticmethod
    def validate_python_type(value, python_type):
        """
        Return True if the python class instantiates the python_type given.
        """
        if python_type == int:
            return any((isinstance(value, python_type), isinstance(value, unicode), value is None))
        else:
            return any((isinstance(value, python_type), value is None))

    @staticmethod
    def validate_GLtype(value, gl_type):
        """
        Return True if the python class matches the given regexp.
        """
        return bool(re.match(gl_type, value))


    @staticmethod
    def validate_type(value, type):
        # if it's callable, than assumes is a primitive class
        if callable(type):
            retval = BaseHandler.validate_python_type(value, type)
            if not retval:
                log.err("-- Invalid python_type, in [%s] expected %s" % (str(value), type))
            return retval
        # value as "{foo:bar}"
        elif isinstance(type, collections.Mapping):
            retval = BaseHandler.validate_jmessage(value, type)
            if not retval:
                log.err("-- Invalid JSON/dict [%s] expected %s" % (str(value), str(type)))
            return retval
        # regexp
        elif isinstance(type, str):
            retval = BaseHandler.validate_GLtype(value, type)
            if not retval:
                log.err("-- Failed Match in regexp [%s] against %s" % (str(value), str(type) ))
            return retval
        # value as "[ type ]"
        elif isinstance(type, collections.Iterable):
            # empty list is ok
            if len(value) == 0:
                return True
            else:
                retval = all(BaseHandler.validate_type(x, type[0]) for x in value)
                if not retval:
                    log.err("-- List validation failed [%s] of %s" % (str(value), str(type)))
                return retval
        else:
            raise AssertionError

    @staticmethod
    def validate_jmessage(jmessage, message_template):
        """
        Takes a string that represents a JSON messages and checks to see if it
        conforms to the message type it is supposed to be.

        This message must be either a dict or a list. This function may be called
        recursively to validate sub-parameters that are also go GLType.

        message: the message string that should be validated

        message_type: the GLType class it should match.
        """
        valid_jmessage = {}
        for key in message_template.keys():
            if key not in jmessage:
                log.debug('key %s not in %s' % (key, jmessage))
                raise errors.InvalidInputFormat('wrong schema: missing %s' % key)
            else:
                valid_jmessage[key] = jmessage[key]

        jmessage = valid_jmessage
        del valid_jmessage

        if not all(BaseHandler.validate_type(jmessage[key], value) for key, value in
                    message_template.iteritems()):
            raise errors.InvalidInputFormat('wrong content 1')

        if not all(BaseHandler.validate_type(value, message_template[key]) for key, value in
                   jmessage.iteritems()):
            raise errors.InvalidInputFormat('wrong content 2')

        return True

    @staticmethod
    def validate_message(message, message_template):
        try:
            jmessage = json.loads(message)
        except ValueError:
            raise errors.InvalidInputFormat("Invalid JSON message")

        if BaseHandler.validate_jmessage(jmessage, message_template):
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
        if self.request.method.lower() == 'post':
            try:
                wrappedMethod = self.get_argument('method')[0]
                print "[^] Forwarding", wrappedMethod, "from POST"
                if wrappedMethod.lower() == 'delete' or \
                        wrappedMethod.lower() == 'put':
                    self.request.method = wrappedMethod.upper()
            except HTTPError:
                pass

    def write_error(self, status_code, **kw):
        exception = kw.get('exception')
        if exception and hasattr(exception, 'error_code'):
            self.set_status(status_code)
            self.finish({'error_message': exception.reason,
                'error_code' : exception.error_code})
        else:
            RequestHandler.write_error(self, status_code, **kw)

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


    def get_current_user(self):
        session_id = self.request.headers.get('X-Session')
        if not session_id:
            return None

        try:
            session = settings.sessions[session_id]
        except KeyError:
            return None
        return session

    @property
    def is_whistleblower(self):
        if not self.current_user or not self.current_user.has_key('role'):
            raise errors.NotAuthenticated

        if self.current_user['role'] == 'wb':
            return True
        else:
            return False


    @property
    def is_receiver(self):
        if not self.current_user or not self.current_user.has_key('role'):
            raise errors.NotAuthenticated

        if self.current_user['role'] == 'receiver':
            return True
        else:
            return False


    def _handle_request_exception(self, e):
        try:
            if isinstance(e.value, (HTTPError, HTTPAuthenticationRequired)):
                e = e.value
        except:
            pass

        if isinstance(e, (HTTPError, HTTPAuthenticationRequired)):
            if self.settings.get("debug") is True and e.log_message:
                format = "%d %s: " + e.log_message
                args = [e.status_code, self._request_summary()] + list(e.args)
                msg = lambda *args: format % args
                log.msg(msg(*args))
            if e.status_code not in httplib.responses:
                log.msg("Bad HTTP status code: %d" % e.status_code)
                return self.send_error(500, exception=e)
            else:
                return self.send_error(e.status_code, exception=e)
        else:
            if self.settings.get("debug") is True:
                log.msg(e)
            log.msg("Uncaught exception %s :: %r" % \
                    (self._request_summary(), self.request))
            type, value, tb = sys.exc_info()
            MailException(type, value, tb)
            return self.send_error(500, exception=e)
