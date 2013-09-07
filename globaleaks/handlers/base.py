# -*- encoding: utf-8 -*-
#
#  base
#  ****
#
# Implementation of BaseHandler, the Cyclone class RequestHandler extended with our
# needings.
#

import httplib
import types
import random
import collections
import json
import re
import sys
import os

from twisted.python.failure import Failure
from twisted.internet import fdesc
from cyclone.web import RequestHandler, HTTPError, HTTPAuthenticationRequired, StaticFileHandler, RedirectHandler
from cyclone.httpserver import HTTPConnection, HTTPRequest, _BadRequestException
from cyclone import escape, httputil
from cyclone.escape import native_str
from io import BytesIO as StringIO
from tempfile import TemporaryFile

from globaleaks.utils import log, sanitize_str, mail_exception
from globaleaks.settings import GLSetting
from globaleaks.rest import errors

content_disposition_re = re.compile(r"attachment; filename=\"(.+)\"")

def validate_host(host_key):
    """
    validate_host checks in the GLSetting list of valid 'Host:' values
    and if matched, return True, else return False
    Is used by all the Web handlers inherit from Cyclone
    """
    # hidden service has not a :port
    if len(host_key) == 22 and host_key[16:22] == '.onion':
        return True

    # strip eventually port
    hostchunk = str(host_key).split(":")
    if len(hostchunk) == 2:
        host_key = hostchunk[0]

    if host_key in GLSetting.accepted_hosts:
        return True

    log.debug("Error in host requested: %s not accepted between: %s " %
              (host_key, GLSetting.accepted_hosts))
    return False

class GLHTTPServer(HTTPConnection):
    file_upload = False
    uploaded_file = {}

    def rawDataReceived(self, data):
        if self.content_length is not None:
            data, rest = data[:self.content_length], data[self.content_length:]
            self.content_length -= len(data)
        else:
            rest = ''

        self._contentbuffer.write(data)
        if self.content_length == 0:
            self._contentbuffer.seek(0, 0)
            if self.file_upload:
                self._on_request_body(self.uploaded_file)
                self.file_upload = False
                self.uploaded_file = {}
            else:
                self._on_request_body(self._contentbuffer.read())
            self.content_length = self._contentbuffer = None
            self.setLineMode(rest)

    def _on_headers(self, data):
        try:
            data = native_str(data.decode("latin1"))
            eol = data.find("\r\n")
            start_line = data[:eol]
            try:
                method, uri, version = start_line.split(" ")
            except ValueError:
                raise _BadRequestException("Malformed HTTP request line")
            if not version.startswith("HTTP/"):
                raise _BadRequestException(
                        "Malformed HTTP version in HTTP Request-Line")
            headers = httputil.HTTPHeaders.parse(data[eol:])
            self._request = HTTPRequest(
                connection=self, method=method, uri=uri, version=version,
                headers=headers, remote_ip=self._remote_ip)

            content_length = int(headers.get("Content-Length", 0))
            self.content_length = content_length

            if content_length:
                if headers.get("Expect") == "100-continue":
                    self.transport.write("HTTP/1.1 100 (Continue)\r\n\r\n")

                if content_length < 100000:
                    self._contentbuffer = StringIO('')
                else:
                    self._contentbuffer = TemporaryFile()
                
                c_d_header = self._request.headers.get("Content-Disposition")
                if c_d_header is not None:
                    c_d_header = c_d_header.lower()
                    m = content_disposition_re.match(c_d_header)
                    if m is None:
                        raise Exception
                    self.file_upload = True
                    self.uploaded_file['filename'] = m.group(1)
                    self.uploaded_file['content_type'] =  self._request.headers.get("Content-Type", 'application/octet-stream')
                    self.uploaded_file['body'] = self._contentbuffer
                    self.uploaded_file['body_len'] = int(content_length)
                
                megabytes = int(content_length) / (1024 * 1024)

                if self.file_upload:
                    limit_type = "upload"
                    limit = GLSetting.memory_copy.maximum_filesize
                else:
                    limit_type = "json"
                    limit = 1000000 # 1MB fixme: add GLSetting.memory_copy.maximum_jsonsize
                                    # is 1MB probably too high. probably this variable must be
                                    # in kB

                # less than 1 megabytes is always accepted
                if megabytes > limit:

                    log.err("Tried %s request larger than expected (%dMb > %dMb)" %
                            (limit_type,
                             megabytes,
                             limit))

                    # In HTTP Protocol errors need to be managed differently than handlers
                    raise errors.HTTPRawLimitReach

                self.setRawMode()
                return

            self.request_callback(self._request)
        except Exception as exception:
            log.msg("Malformed HTTP request from %s: %s" % (self._remote_ip, exception))
            log.exception(exception)
            if self._request:
                self._request.finish()
            if self.transport:
                self.transport.loseConnection()

    def _on_request_body(self, data):
        try:
            self._request.body = data
            content_type = self._request.headers.get("Content-Type", "")
            if self._request.method in ("POST", "PATCH", "PUT"):
                if content_type.startswith("application/x-www-form-urlencoded"):
                    raise errors.InvalidInputFormat("content type application/x-www-form-urlencoded not supported")
                elif content_type.startswith("multipart/form-data"):
                    raise errors.InvalidInputFormat("content type multipart/form-data not supported")
            self.request_callback(self._request)
        except Exception as exception:
            log.msg("Malformed HTTP request from %s: %s" % (self._remote_ip, exception))
            log.exception(exception)
            if self._request:
                self._request.finish()
            if self.transport:
                self.transport.loseConnection()


class BaseBaseHandler(RequestHandler):
    xsrf_cookie_name = "XSRF-TOKEN"

    def set_default_headers(self):
        # In this function are written some security enforcements
        # related to WebServer versioning and XSS attacks.
        """
            just reading the property is enough to
            set the cookie as a side effect.
        """
        self.xsrf_token

        # to avoid version attacks
        self.set_header("Server", "globaleaks")

        # to reduce possibility for XSS attacks.
        self.set_header("X-Content-Type-Options", "nosniff")

        # to mitigate information leakage on Browser/Proxy Cache
        self.set_header("Cache-control", "no-cache, no-store")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "Mon, 01-Jan-1990 00:00:00")

        if not GLSetting.cyclone_debug:
            # to mitigate clickjaking attacks on iframes
            self.set_header("X-Frame-Options", "deny")

        lang = self.request.headers.get('GL-Language', None)

        if not lang:
            lang = self.request.headers.get('Accepted-Language', None)

        # TODO if not lang default of the Node (need update DB)
        if not lang:
           lang = 'en'

        # At the moment the default is 'en', but need to be a Node value
        self.request.language = lang

    def check_xsrf_cookie(self):
        """
            Override needed to change name of header name
        """
        token = self.request.headers.get("X-XSRF-TOKEN")
        if not token:
            raise HTTPError(403, "X-XSRF-TOKEN argument missing from POST")
        if self.xsrf_token != token:
            raise HTTPError(403, "XSRF cookie does not match POST argument")

class BaseHandler(BaseBaseHandler):
    @staticmethod
    def validate_python_type(value, python_type):
        """
        Return True if the python class instantiates the python_type given,
            'int' fields are accepted also as 'unicode' but cast on base 10
            before validate them
            'bool' fields are accepted also as 'true' 'false' because this
            happen on angular.js
        """
        if value is None:
            return True

        if python_type == int:
            try:
                int(value)
                return True
            except Exception:
                return False

        if python_type == bool:
            if value == u'true' or value == u'false':
                return True

        return isinstance(value, python_type)

    @staticmethod
    def validate_GLtype(value, gl_type):
        """
        Return True if the python class matches the given regexp.
        """
        if isinstance(value, str):
            return bool(re.match(gl_type, value))
        else:
            return False

    @staticmethod
    def validate_type(value, type):
        # if it's callable, than assumes is a primitive class
        if callable(type):
            retval = BaseHandler.validate_python_type(value, type)
            if not retval:
                log.err("-- Invalid python_type, in [%s] expected %s" % (value, type))
            return retval
        # value as "{foo:bar}"
        elif isinstance(type, collections.Mapping):
            retval = BaseHandler.validate_jmessage(value, type)
            if not retval:
                log.err("-- Invalid JSON/dict [%s] expected %s" % (value, type))
            return retval
        # regexp
        elif isinstance(type, str):
            retval = BaseHandler.validate_GLtype(value, type)
            if not retval:
                log.err("-- Failed Match in regexp [%s] against %s" % (value, type))
            return retval
        # value as "[ type ]"
        elif isinstance(type, collections.Iterable):
            # empty list is ok
            if len(value) == 0:
                return True
            else:
                retval = all(BaseHandler.validate_type(x, type[0]) for x in value)
                if not retval:
                    log.err("-- List validation failed [%s] of %s" % (value, type))
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
                log.err('key %s not in %s' % (key, jmessage))
                raise errors.InvalidInputFormat('wrong schema: missing %s' % key)
            else:
                valid_jmessage[key] = jmessage[key]

        jmessage = valid_jmessage
        del valid_jmessage

        for key, value in message_template.iteritems():
            if not BaseHandler.validate_type(jmessage[key], value):
                raise errors.InvalidInputFormat("REST integrity check 1, fail in %s" % key)

        for key, value in jmessage.iteritems():
            if not BaseHandler.validate_type(value, message_template[key]):
                raise errors.InvalidInputFormat("REST integrity check 2, fail in %s" % key)

        return True

    @staticmethod
    def validate_message(message, message_template):
        try:
            jmessage = json.loads(message)
        except ValueError:
            raise errors.InvalidInputFormat("Invalid JSON format")

        if BaseHandler.validate_jmessage(jmessage, message_template):
            return jmessage


    def output_stripping(self, message, message_template):
        """
        @param message: the serialized dict received
        @param message_template: the answers definition
        @return: a dict or a list without the unwanted keys
        """
        pass

    def initialize(self):
        pass

    def on_connection_close(self, *args, **kwargs):
        pass

    requestTypes = {}
    def prepare(self):
        """
        This method is called by cyclone, and is implemented to
        handle the POST fallback, in environment where PUT and DELETE
        method may not be used.
        Is used also to log the complete request, if the option is
        command line specified
        """

        """
            just reading the property is enough to
            set the cookie as a side effect).
        """
        self.xsrf_token

        if not validate_host(self.request.host):
            raise errors.InvalidHostSpecified

        # if 0 is infinite logging of the requests
        if GLSetting.cyclone_debug >= 0:

            GLSetting.cyclone_debug_counter += 1

            try:
                content = (">" * 15)
                content += (" Request %d " % GLSetting.cyclone_debug_counter)
                content += (">" * 15) + "\n\n" 

                content += self.request.method + " " + self.request.full_url() + "\n\n"

                content += "headers:\n"
                for k, v in self.request.headers.get_all():
                    content += "%s: %s\n" % (k, v)

                if type(self.request.body) == dict and 'body' in self.request.body:
                    # this is needed due to cyclone hack for file uploads
                    body = self.request.body['body'].read()
                else:
                    body = self.request.body

                if len(body):
                    content += "\nbody:\n" + body + "\n"

                self.do_verbose_log(content)

            except Exception as excep:
                log.err("JSON logging fail (prepare): %s" % excep.message)
                return

            # save in the request the numeric ID of the request, so the answer can be correlated
            self.globaleaks_io_debug = GLSetting.cyclone_debug_counter

            if GLSetting.cyclone_debug > 0 and GLSetting.cyclone_debug_counter >= GLSetting.cyclone_debug:
                log.debug("Reached I/O logging limit of %d requests: disabling" % GLSetting.cyclone_debug)
                GLSetting.cyclone_debug = -1


    def flush(self, include_footers=False):
        """
        This method is used internally by Cyclone,
        Cyclone specify the function on_finish but in that time the request is already flushed,
        so overwrite flush() was the easiest way to achieve our collection.

        It's here implemented to supports the I/O logging if requested
        with the command line options --io $number_of_request_recorded
        """
        if hasattr(self, 'globaleaks_io_debug'):
            try:
                content = ("<" * 15)
                content += (" Response %d " % self.globaleaks_io_debug)
                content += ("<" * 15) + "\n\n"
                content += "status code: " + str(self._status_code) + "\n\n"

                content += "headers:\n"
                for k, v in self._headers.iteritems():
                    content += "%s: %s\n" % (k, v)

                if self._write_buffer is not None:
                    content += "\nbody: " + str(self._write_buffer) + "\n"

                self.do_verbose_log(content)
            except Exception as excep:
                log.err("JSON logging fail (flush): %s" % excep.message)
                return

        RequestHandler.flush(self, include_footers)


    def do_verbose_log(self, content):
        """
        Record in the verbose log the content as defined by Cyclone wrappers.
        """
        content = sanitize_str(content)        

        try:
            with open(GLSetting.cyclonelogfile, 'a+') as fd:
                fdesc.writeToFD(fd.fileno(), content + "\n")
        except Exception as excep:
            log.err("Unable to open %s: %s" % (logfpath, excep.message))

    def write_error(self, status_code, **kw):
        exception = kw.get('exception')
        if exception and hasattr(exception, 'error_code'):
            self.set_status(status_code)
            self.finish({'error_message': exception.reason,
                'error_code' : exception.error_code,
                'arguments': exception.arguments })
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

    @property
    def current_user(self):
        session_id = self.request.headers.get('X-Session')
        if not session_id:
            return None

        try:
            session = GLSetting.sessions[session_id]
        except KeyError:
            return None
        return session

    @property
    def is_whistleblower(self):
        if not self.current_user or not self.current_user.has_key('role'):
            raise errors.NotAuthenticated

        return self.current_user['role'] == 'wb'

    @property
    def is_receiver(self):
        if not self.current_user or not self.current_user.has_key('role'):
            raise errors.NotAuthenticated

        return self.current_user['role'] == 'receiver'

    def _handle_request_exception(self, e):
        # sys.exc_info() does not always work at this stage
        if isinstance(e, Failure):
            exc_type = e.type
            exc_value = e.value
            exc_tb = e.getTracebackObject()
            e = e.value
        else:
            exc_type, exc_value, exc_tb = sys.exc_info()
 
        if isinstance(e, (HTTPError, HTTPAuthenticationRequired)):
            if GLSetting.cyclone_debug and e.log_message:
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
            log.err("Uncaught exception %s %s %s" % (exc_type, exc_value, exc_tb) )
            if GLSetting.cyclone_debug:
                log.msg(e)
            mail_exception(exc_type, exc_value, exc_tb)
            return self.send_error(500, exception=e)

class BaseStaticFileHandler(BaseBaseHandler, StaticFileHandler):
    def prepare(self):
        """
        This method is called by cyclone,and perform 'Host:' header
        validation using the same 'validate_host' function used by
        BaseHandler. but BaseHandler manage the REST API,..
        BaseStaticFileHandler manage all the statically served files.
        """
        if not validate_host(self.request.host):
            raise errors.InvalidHostSpecified


class BaseRedirectHandler(BaseBaseHandler, RedirectHandler):
    def prepare(self):
        """
        Same reason of StaticFileHandler
        """
        if not validate_host(self.request.host):
            raise errors.InvalidHostSpecified
