# -*- encoding: utf-8 -*-
"""
Implementation of BaseHandler, the Cyclone class RequestHandler postponeed with
our needs.
"""

import collections
import httplib
import json
import mimetypes
import os
import re
import sys
import time
import types

from StringIO import StringIO

from twisted.internet import fdesc
from twisted.internet.defer import inlineCallbacks
from twisted.python.failure import Failure

from cyclone import escape, httputil
from cyclone.escape import native_str
from cyclone.httpserver import HTTPConnection, HTTPRequest, _BadRequestException
from cyclone.web import RequestHandler, HTTPError, HTTPAuthenticationRequired, RedirectHandler

from globaleaks.event import outcoming_event_monitored, EventTrack
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.security import GLSecureTemporaryFile, directory_traversal_check, generateRandomKey
from globaleaks.utils.mailutils import mail_exception_handler, send_exception_email
from globaleaks.utils.utility import log, log_encode_html, datetime_now, deferred_sleep


HANDLER_EXEC_TIME_THRESHOLD = 30

GLUploads = {}


def validate_host(host_key):
    """
    validate_host checks in the GLSettings list of valid 'Host:' values
    and if matched, return True, else return False
    Is used by all the Web handlers inherit from Cyclone
    """
    # strip eventually port
    hostchunk = str(host_key).split(":")
    if len(hostchunk) == 2:
        host_key = hostchunk[0]

    # hidden service has not a :port
    if re.match(r'^[0-9a-z]{16}\.onion$', host_key):
        return True

    if host_key != '' and host_key in GLSettings.accepted_hosts:
        return True

    log.debug("Error in host requested: %s not accepted between: %s " %
              (host_key, GLSettings.accepted_hosts))

    return False


class GLHTTPConnection(HTTPConnection):
    def __init__(self):
        self.uploaded_file = {}

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
            try:
                headers = httputil.HTTPHeaders.parse(data[eol:])
                content_length = int(headers.get("Content-Length", 0))
            except ValueError:
                raise _BadRequestException(
                    "Malformed Content-Length header")
            self._request = HTTPRequest(
                connection=self, method=method, uri=uri, version=version,
                headers=headers, remote_ip=self._remote_ip)

            if content_length:
                megabytes = int(content_length) / (1024 * 1024)
                if megabytes > GLSettings.memory_copy.maximum_filesize:
                    raise _BadRequestException("Request exceeded size limit %d" %
                                               GLSettings.memory_copy.maximum_filesize)

                if headers.get("Expect") == "100-continue":
                    self.transport.write("HTTP/1.1 100 (Continue)\r\n\r\n")

                if content_length < 100000:
                    self._contentbuffer = StringIO()
                else:
                    self._contentbuffer = GLSecureTemporaryFile(GLSettings.tmp_upload_path)

                self.content_length = content_length
                self.setRawMode()
                return

            self.request_callback(self._request)
        except _BadRequestException as e:
            log.msg("Exception while handling HTTP request from %s: %s" % (self._remote_ip, e))
            self.transport.loseConnection()


class BaseHandler(RequestHandler):
    handler_exec_time_threshold = HANDLER_EXEC_TIME_THRESHOLD

    filehandler = False

    def __init__(self, application, request, **kwargs):
        RequestHandler.__init__(self, application, request, **kwargs)

        self.name = type(self).__name__

        self.handler_time_analysis_begin()
        self.handler_request_logging_begin()

        self.req_id = GLSettings.requests_counter
        GLSettings.requests_counter += 1

        self.request.language = GLSettings.memory_copy.default_language
        self.request.import_export = None

    def set_default_headers(self):
        """
        In this function are written some security enforcements
        related to WebServer versioning and XSS attacks.

        This is the first function called when a new request reach GLB
        """
        self.request.start_time = datetime_now()

        # to avoid version attacks
        self.set_header("Server", "globaleaks")

        # to reduce possibility for XSS attacks.
        self.set_header("X-Content-Type-Options", "nosniff")
        self.set_header("X-XSS-Protection", "1; mode=block")

        # to mitigate information leakage on Browser/Proxy Cache
        self.set_header("Cache-control", "no-cache, no-store, must-revalidate")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "-1")

        # to avoid information leakage via referrer
        self.set_header("Content-Security-Policy", "referrer no-referrer")

        # to avoid Robots spidering, indexing, caching
        self.set_header("X-Robots-Tag", "noindex")

        # to mitigate clickjaking attacks on iframes allowing only same origin
        # same origin is needed in order to include svg and other html <object>
        if not GLSettings.memory_copy.allow_iframes_inclusion:
            self.set_header("X-Frame-Options", "sameorigin")

        if 'import' in self.request.arguments:
            self.request_type = 'import'
        elif 'export' in self.request.arguments:
            self.request_type = 'export'

        self.request.language = self.request.headers.get('GL-Language', GLSettings.memory_copy.default_language)

    @staticmethod
    def validate_python_type(value, python_type):
        """
        Return True if the python class instantiates the specified python_type.
        """
        if value is None:
            return True

        if python_type == requests.SkipSpecificValidation:
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
    def validate_regexp(value, type):
        """
        Return True if the python class matches the given regexp.
        """
        try:
            value = unicode(value)
        except Exception:
            return False

        return bool(re.match(type, value))

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
            retval = BaseHandler.validate_regexp(value, type)
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
        if isinstance(message_template, dict):
            success_check = 0
            keys_to_strip = []
            for key, value in jmessage.iteritems():
                if key not in message_template:
                    # strip whatever is not validated
                    #
                    # reminder: it's not possible to raise an exception for the
                    # in case more values are presenct because it's normal that the
                    # client will send automatically more data.
                    #
                    # e.g. the client will always send 'creation_date' attributs of
                    #      objects and attributes like this are present generally only
                    #      from the second request on.
                    #
                    keys_to_strip.append(key)
                    continue

                if not BaseHandler.validate_type(value, message_template[key]):
                    log.err("Received key %s: type validation fail " % key)
                    raise errors.InvalidInputFormat("Key (%s) type validation failure" % key)
                success_check += 1

            for key in keys_to_strip:
                del jmessage[key]

            for key, value in message_template.iteritems():
                if key not in jmessage.keys():
                    log.debug("Key %s expected but missing!" % key)
                    log.debug("Received schema %s - Expected %s" %
                              (jmessage.keys(), message_template.keys()))
                    raise errors.InvalidInputFormat("Missing key %s" % key)

                if not BaseHandler.validate_type(jmessage[key], value):
                    log.err("Expected key: %s type validation failure" % key)
                    raise errors.InvalidInputFormat("Key (%s) double validation failure" % key)
                success_check += 1

            if success_check == len(message_template.keys()) * 2:
                return True
            else:
                log.err("Success counter double check failure: %d" % success_check)
                raise errors.InvalidInputFormat("Success counter double check failure")

        elif isinstance(message_template, list):
            ret = all(BaseHandler.validate_type(x, message_template[0]) for x in jmessage)
            if not ret:
                raise errors.InvalidInputFormat("Not every element in %s is %s" %
                                                (jmessage, message_template[0]))
            return True

        else:
            raise errors.InvalidInputFormat("invalid json massage: expected dict or list")


    @staticmethod
    def validate_message(message, message_template):
        try:
            jmessage = json.loads(message)
        except ValueError:
            raise errors.InvalidInputFormat("Invalid JSON format")

        if BaseHandler.validate_jmessage(jmessage, message_template):
            return jmessage

        raise errors.InvalidInputFormat("Unexpected condition!?")


    def output_stripping(self, message, message_template):
        """
        @param message: the serialized dict received
        @param message_template: the answers definition
        @return: a dict or a list without the unwanted keys
        """
        pass

    def on_connection_close(self, *args, **kwargs):
        pass

    def prepare(self):
        """
        Here is implemented:
          - The performance analysts
          - the Request/Response logging
        """
        if not validate_host(self.request.host):
            raise errors.InvalidHostSpecified

    def on_finish(self):
        """
        Here is implemented:
          - The performance analysts
          - the Request/Response logging
        """
        # file uploads works on chunk basis so that we count 1 the file upload
        # as a whole in function get_file_upload()
        if not self.filehandler:
            for event in outcoming_event_monitored:
                if event['status_checker'](self._status_code) and \
                        event['method'] == self.request.method and \
                        event['handler_check'](self.request.uri):
                    EventTrack(event, self.request.request_time())

        self.handler_time_analysis_end()
        self.handler_request_logging_end()

    def do_verbose_log(self, content):
        """
        Record in the verbose log the content as defined by Cyclone wrappers.

        This option is only available in devel mode and intentionally does not filter
        any input/output; It should be used only for debug purposes.
        """

        try:
            with open(GLSettings.httplogfile, 'a+') as fd:
                fdesc.writeToFD(fd.fileno(), content + "\n")
        except Exception as excep:
            log.err("Unable to open %s: %s" % (GLSettings.httplogfile, excep))

    def write_file(self, filepath):
        try:
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(GLSettings.file_chunk_size)
                    if len(chunk) == 0:
                        break
                    self.write(chunk)
        except IOError as srcerr:
            log.err("Unable to open %s: %s " % (filepath, srcerr.strerror))

    def write_error(self, status_code, **kw):
        exception = kw.get('exception')
        if exception and hasattr(exception, 'error_code'):
            error_dict = {
                'error_message': exception.reason,
                'error_code': exception.error_code
            }

            if hasattr(exception, 'arguments'):
                error_dict.update({'arguments': exception.arguments})
            else:
                error_dict.update({'arguments': []})

            self.set_status(status_code)
            self.finish(error_dict)
        else:
            RequestHandler.write_error(self, status_code, **kw)

    def write(self, chunk):
        """
        This is a monkey patch to RequestHandler to allow us to serialize also
        json list objects.
        """
        if isinstance(chunk, types.ListType):
            self.set_header("Content-Type", "application/json")
            chunk = escape.json_encode(chunk)

        RequestHandler.write(self, chunk)

    @inlineCallbacks
    def uniform_answers_delay(self):
        """
        @return: nothing.

        the function perform a sleep uniforming requests to the side_channels_guard
        defined in GLSettings.side_channels_guard in order to counteract some
        side channel attacks.
        """
        request_time = self.request.request_time()
        needed_delay = GLSettings.side_channels_guard - request_time

        if needed_delay > 0:
            yield deferred_sleep(needed_delay)

    @property
    def current_user(self):
        # Check for header based authentication
        session_id = self.request.headers.get('X-Session')

        # Check for GET/POST based authentication.
        if session_id is None:
            session_id = self.get_argument('session', default=None)

        if session_id is None:
            return None

        return GLSettings.sessions.get(session_id)

    def get_file_upload(self):
        try:
            if len(self.request.files) != 1:
                raise errors.InvalidInputFormat("cannot accept more than a file upload at once")

            chunk_size = len(self.request.files['file'][0]['body'])
            total_file_size = int(self.request.arguments['flowTotalSize'][0]) if 'flowTotalSize' in self.request.arguments else chunk_size
            flow_identifier = self.request.arguments['flowIdentifier'][0] if 'flowIdentifier' in self.request.arguments else generateRandomKey(10)

            if ((chunk_size / (1024 * 1024)) > GLSettings.memory_copy.maximum_filesize or
                (total_file_size / (1024 * 1024)) > GLSettings.memory_copy.maximum_filesize):
                log.err("File upload request rejected: file too big")
                raise errors.FileTooBig(GLSettings.memory_copy.maximum_filesize)

            if flow_identifier not in GLUploads:
                f = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
                GLUploads[flow_identifier] = f
            else:
                f = GLUploads[flow_identifier]

            f.write(self.request.files['file'][0]['body'])

            if 'flowChunkNumber' in self.request.arguments and 'flowTotalChunks' in self.request.arguments:
                if self.request.arguments['flowChunkNumber'][0] != self.request.arguments['flowTotalChunks'][0]:
                    return None

            uploaded_file = {}
            uploaded_file['filename'] = self.request.files['file'][0]['filename']
            uploaded_file['content_type'] = self.request.files['file'][0]['content_type']
            uploaded_file['body_len'] = total_file_size
            uploaded_file['body_filepath'] = f.filepath
            uploaded_file['body'] = f

            upload_time = time.time() - f.creation_date

            # file uploads works on chunk basis so that we count 1 the file upload
            # as a whole in function get_file_upload()
            for event in outcoming_event_monitored:
                if event['status_checker'](self._status_code) and \
                        event['method'] == self.request.method and \
                        event['handler_check'](self.request.uri):
                    EventTrack(event, upload_time)

            return uploaded_file

        except errors.FileTooBig:
            raise  # propagate the exception

        except Exception as exc:
            log.err("Error while handling file upload %s" % exc)
            return None

    def _handle_request_exception(self, e):
        if isinstance(e, Failure):
            exc_type = e.type
            exc_value = e.value
            exc_tb = e.getTracebackObject()
            e = e.value
        else:
            exc_type, exc_value, exc_tb = sys.exc_info()

        if isinstance(e, (HTTPError, HTTPAuthenticationRequired)):
            if GLSettings.log_requests_responses and e.log_message:
                string_format = "%d %s: " + e.log_message
                args = [e.status_code, self._request_summary()] + list(e.args)
                msg = lambda *args: string_format % args
                log.msg(msg(*args))
            if e.status_code not in httplib.responses:
                log.msg("Bad HTTP status code: %d" % e.status_code)
                return self.send_error(500, exception=e)
            else:
                return self.send_error(e.status_code, exception=e)
        else:
            log.err("Uncaught exception %s %s %s" % (exc_type, exc_value, exc_tb))
            if GLSettings.log_requests_responses:
                log.msg(e)
            mail_exception_handler(exc_type, exc_value, exc_tb)
            return self.send_error(500, exception=e)

    def handler_time_analysis_begin(self):
        self.start_time = time.time()

    def handler_time_analysis_end(self):
        """
        If the software is running with the option -S --stats (GLSetting.log_timing_stats)
        then we are doing performance testing, having our mailbox spammed is not important,
        so we just skip to report the anomaly.
        """
        current_run_time = time.time() - self.start_time

        if current_run_time > self.handler_exec_time_threshold:
            error = "Handler [%s] exceeded exec threshold (of %d secs) with an execution time of %.2f seconds" % \
                    (self.name, self.handler_exec_time_threshold, current_run_time)
            log.err(error)

            send_exception_email(error, mail_reason="Handler Time Exceeded")

        if GLSettings.log_timing_stats:
            TimingStatsHandler.log_measured_timing(self.request.method, self.request.uri, self.start_time, current_run_time)


    def handler_request_logging_begin(self):
        if GLSettings.devel_mode and GLSettings.log_requests_responses:
            try:
                content = (">" * 15)
                content += (" Request %d " % GLSettings.requests_counter)
                content += (">" * 15) + "\n\n"

                content += self.request.method + " " + self.request.full_url() + "\n\n"

                content += "request-headers:\n"
                for k, v in self.request.headers.get_all():
                    content += "%s: %s\n" % (k, v)

                if type(self.request.body) == dict and 'body' in self.request.body:
                    # this is needed due to cyclone hack for file uploads
                    body = self.request.body['body'].read()
                else:
                    body = self.request.body

                if len(body):
                    content += "\nrequest-body:\n" + body + "\n"

                self.do_verbose_log(content)

            except Exception as excep:
                log.err("HTTP Request logging fail: %s" % excep.message)
                return

    def handler_request_logging_end(self):
        if GLSettings.devel_mode and GLSettings.log_requests_responses:
            try:
                content = ("<" * 15)
                content += (" Response %d " % self.req_id)
                content += ("<" * 15) + "\n\n"
                content += "\nbody: " + str(self._write_buffer) + "\n"

                self.do_verbose_log(content)
            except Exception as excep:
                log.err("HTTP Requests/Responses logging fail (end): %s" % excep.message)


class BaseStaticFileHandler(BaseHandler):
    def initialize(self, path=None):
        if path is None:
            path = GLSettings.static_path

        self.root = "%s%s" % (os.path.abspath(path), os.path.sep)

    def get(self, path):
        if path == '':
            path = 'index.html'

        path = self.parse_url_path(path)
        abspath = os.path.abspath(os.path.join(self.root, path))

        directory_traversal_check(self.root, abspath)

        if not os.path.exists(abspath) or not os.path.isfile(abspath):
            raise HTTPError(404)

        mime_type, encoding = mimetypes.guess_type(abspath)
        if mime_type:
            self.set_header("Content-Type", mime_type)

        self.write_file(abspath)

    def parse_url_path(self, url_path):
        if os.path.sep != "/":
            url_path = url_path.replace("/", os.path.sep)
        return url_path


class BaseRedirectHandler(BaseHandler, RedirectHandler):
    pass


class TimingStatsHandler(BaseHandler):
    TimingsTracker = []

    @staticmethod
    def log_measured_timing(method, uri, start_time, run_time):
        if not GLSettings.log_timing_stats:
            return

        if uri == '/s/timings':
            return

        TimingStatsHandler.TimingsTracker = \
            TimingStatsHandler.TimingsTracker[999:] if len(TimingStatsHandler.TimingsTracker) > 999 else TimingStatsHandler.TimingsTracker

        if method == 'POST' and uri == '/token':
            category = 'token'
        elif method == 'PUT' and uri.startswith('/submission'):
            category = 'submission'
        elif method == 'POST' and uri == '/wbtip/comments':
            category = 'comment'
        elif method == 'JOB' and uri == 'Delivery':
            category = 'delivery'
        else:
            category = 'uncategorized'

        TimingStatsHandler.TimingsTracker.append({
            'category': category,
            'method': method,
            'uri': uri,
            'start_time': start_time,
            'run_time': run_time
        })

    def get(self):
        csv = "category,method,uri,start_time,run_time\n"
        for measure in TimingStatsHandler.TimingsTracker:
            csv += "%s,%s,%s,%s,%d\n" % (measure['category'],
                                         measure['method'],
                                         measure['uri'],
                                         measure['start_time'],
                                         measure['run_time'])
        self.set_status(200)
        self.finish(csv)
