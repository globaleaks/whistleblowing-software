# -*- encoding: utf-8 -*-
import base64
import collections
import functools
import json
import mimetypes
import os
import re
import shutil
import sys
import time
import types
import urlparse

from datetime import datetime

from twisted.internet import fdesc, defer
from twisted.internet.defer import inlineCallbacks
from twisted.python.failure import Failure
from twisted.web.resource import Resource
from twisted.web.static import File

from globaleaks.event import track_handler
from globaleaks.rest import errors, requests
from globaleaks.security import GLSecureTemporaryFile, directory_traversal_check, generateRandomKey
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import mail_exception_handler, send_exception_email
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import log, deferred_sleep

HANDLER_EXEC_TIME_THRESHOLD = 30

GLUploads = {}

class GLSessionsFactory(TempDict):
  '''Extends TempDict to provide session management functions ontop of temp session keys'''

  def revoke_all_sessions(self, user_id):
      for other_session in GLSessions.values():
          if other_session.user_id == user_id:
              log.debug("Revoking old session for %s" % user_id)
              GLSessions.delete(other_session.id)

GLSessions = GLSessionsFactory(timeout=GLSettings.authentication_lifetime)

# https://github.com/globaleaks/GlobaLeaks/issues/1601
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
mimetypes.add_type('application/x-font-ttf', '.ttf')
mimetypes.add_type('application/woff', '.woff')
mimetypes.add_type('application/woff2', '.woff2')


def write_upload_plaintext_to_disk(uploaded_file, destination):
    """
    @param uploaded_file: uploaded_file data struct
    @param the file destination
    @return: a descriptor dictionary for the saved file
    """
    try:
        if os.path.exists(destination):
            log.err('Overwriting file %s with %d bytes' % (destination, uploaded_file['size']))
        else:
            log.debug('Creating file %s with %d bytes' % (destination, uploaded_file['size']))

        with open(destination, 'w+') as fd:
            uploaded_file['body'].seek(0, 0)
            data = uploaded_file['body'].read(4000)
            while data != '':
                os.write(fd.fileno(), data)
                data = uploaded_file['body'].read(4000)
    finally:
        uploaded_file['body'].close()
        uploaded_file['path'] = destination

    return uploaded_file


def write_upload_encrypted_to_disk(uploaded_file, destination):
    """
    @param uploaded_file: uploaded_file data struct
    @param the file destination
    @return: a descriptor dictionary for the saved file
    """
    log.debug("Moving encrypted bytes %d from file [%s] %s => %s" %
        (uploaded_file['size'],
         uploaded_file['name'],
         uploaded_file['path'],
         destination)
    )

    shutil.move(uploaded_file['path'], destination)

    uploaded_file['path'] = destination

    return uploaded_file



class StaticFileProducer(object):
    """Streaming producter for files

    @ivar handler: The L{IRequest} to write the contents of the file to.
    @ivar fileObject: The file the contents of which to write to the request.
    """
    bufferSize = GLSettings.file_chunk_size

    def __init__(self, handler, filePath):
        self.finish = defer.Deferred()
        self.handler = handler
        self.fileSize = os.stat(filePath).st_size
        self.fileObject = open(filePath, "rb")
        self.bytesWritten = 0

    def start(self):
        self.handler.request.registerProducer(self, False)
        return self.finish

    def resumeProducing(self):
        try:
            if not self.handler:
                return

            data = self.fileObject.read(self.bufferSize)
            if data:
                self.bytesWritten += len(data)
                self.handler.request.write(data)

            if self.bytesWritten == self.fileSize:
                self.stopProducing()
        except:
            self.stopProducing()
            raise

    def stopProducing(self):
        self.fileObject.close()
        self.handler.request.unregisterProducer()
        self.handler.request.finish()
        self.handler = None
        self.finish.callback(None)


class GLSession(object):
    expireCall = None # attached to object by tempDict

    def __init__(self, user_id, user_role, user_status):
        self.id = generateRandomKey(42)
        self.user_id = user_id
        self.user_role = user_role
        self.user_status = user_status

        GLSessions.set(self.id, self)

    def getTime(self):
        return self.expireCall.getTime()

    def __repr__(self):
        return "%s %s expire in %s" % (self.user_role, self.user_id, self.expireCall)


class BaseHandler(object):
    decorated = False
    serialize_lists = True
    handler_exec_time_threshold = HANDLER_EXEC_TIME_THRESHOLD
    uniform_answer_time = False
    cache_resource = False
    invalidate_cache = False

    def __init__(self, request):
        self.request = request
        self.request.start_time = datetime.now()

        self.name = type(self).__name__

        self.req_id = GLSettings.requests_counter
        GLSettings.requests_counter += 1

        self.request.headers = self.request.getAllHeaders()

        self.client_ip = request.headers.get('X-Forwarded-For', None)
        if self.client_ip is None:
            self.client_ip = self.request.getClientIP()

        self.client_using_tor = self.client_ip in GLSettings.state.tor_exit_set

        if self.should_redirect_tor():
           self.redirect_tor()

        if self.should_redirect_https():
            self.redirect_https()

        language = self.request.headers.get('gl-language')

        if language is None:
            for l in self.parse_accept_language_header():
                if l in GLSettings.memory_copy.languages_enabled:
                    language = l
                    break

        if language is None or language not in GLSettings.memory_copy.languages_enabled:
            language = GLSettings.memory_copy.default_language

        self.request.language = language
        self.request.setHeader(b'content-language', language)

        self.set_default_headers()

    def set_default_headers(self):
        # to avoid version attacks
        self.request.setHeader("Server", "Globaleaks")

        # to reduce possibility for XSS attacks.
        self.request.setHeader("X-Content-Type-Options", "nosniff")
        self.request.setHeader("X-XSS-Protection", "1; mode=block")

        # to disable caching
        self.request.setHeader("Cache-control", "no-cache, no-store, must-revalidate")
        self.request.setHeader("Pragma", "no-cache")
        self.request.setHeader("Expires", "-1")

        # to avoid information leakage via referrer
        self.request.setHeader("Referrer-Policy", "no-referrer")

        # to avoid Robots spidering, indexing, caching
        if not GLSettings.memory_copy.allow_indexing:
            self.request.setHeader("X-Robots-Tag", "noindex")

        # to mitigate clickjaking attacks on iframes allowing only same origin
        # same origin is needed in order to include svg and other html <object>
        if not GLSettings.memory_copy.allow_iframes_inclusion:
            self.request.setHeader("X-Frame-Options", "sameorigin")

    def write(self, chunk):
        self.request.write(chunk)

    def parse_accept_language_header(self):
        if "accept-language" in self.request.headers:
            languages = self.request.headers["accept-language"].split(",")
            locales = []
            for language in languages:
                parts = language.strip().split(";")
                if len(parts) > 1 and parts[1].startswith("q="):
                    try:
                        score = float(parts[1][2:])
                    except (ValueError, TypeError):
                        score = 0.0
                else:
                    score = 1.0
                locales.append((parts[0], score))
            if locales:
                locales.sort(key=lambda pair: pair[1], reverse=True)
                return [l[0] for l in locales]

        return GLSettings.memory_copy.default_language

    @staticmethod
    def authentication(f, roles):
        """
        Decorator for authenticated sessions.
        """
        def wrapper(self, *args, **kwargs):
            if GLSettings.memory_copy.basic_auth:
                cls.basic_auth()

            if '*' in roles:
               return f(self, *args, **kwargs)

            if 'unauthenticated' in roles:
                if self.current_user:
                    raise errors.InvalidAuthentication

                return f(self, *args, **kwargs)

            if not self.current_user:
               raise errors.NotAuthenticated

            if self.current_user.user_role in roles:
               log.debug("Authentication OK (%s)" % self.current_user.user_role)
               return f(self, *args, **kwargs)

            raise errors.InvalidAuthentication

        return wrapper

    @staticmethod
    def https_enabled(f):
        """
        Decorator that enforces https_enabled is set to True
        """
        def wrapper(*args, **kwargs):
            if not GLSettings.memory_copy.private.https_enabled:
                raise errors.FailedSanityCheck()

            return f(*args, **kwargs)

        return wrapper

    @staticmethod
    def https_disabled(f):
        """
        Decorator that enforces https_enabled is set to False
        """
        def wrapper(*args, **kwargs):
            if GLSettings.memory_copy.private.https_enabled:
                raise errors.FailedSanityCheck()

            return f(*args, **kwargs)

        return wrapper

    def basic_auth(self):
        msg = None
        if "authorization" in self.request.headers:
            try:
                auth_type, data = self.request.headers["authorization"].split()
                usr, pwd = base64.b64decode(data).split(":", 1)
                if auth_type != "Basic" or \
                    usr != GLSettings.memory_copy.basic_auth_username or \
                    pwd != GLSettings.memory_copy.basic_auth_password:
                    msg = "Authentication failed"
            except AssertionError:
                msg = "Authentication failed"
        else:
            msg = "Authentication required"

        if msg is not None:
            self.request.setHeader("WWW-Authenticate", "Basic realm=\"globaleaks\"")
            raise errors.HTTPAuthenticationRequired()

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
                    # in case more values are present because it's normal that the
                    # client will send automatically more data.
                    #
                    # e.g. the client will always send 'creation_date' attributes of
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

    def redirect(self, url):
        self.request.setResponseCode(301)
        self.request.setHeader(b"location", url)
        self.request.finish()

    def redirect_https(self):
        in_url = self.request.uri

        pr = urlparse.urlsplit(in_url)

        out_url = urlparse.urlunsplit(('https', pr.hostname, pr.path, pr.query, pr.fragment))

        if out_url == in_url:
            raise errors.InternalServerError('Should redirect to https: %s' % out_url)

        self.redirect(out_url)

    def redirect_tor(self, onion_addr):
        in_url = self.request.uri

        _, _, path, query, frag = urlparse.urlsplit(in_url)

        out_url = urlparse.urlunsplit(('http', onion_addr, path, query, frag))

        if out_url == in_url:
            raise errors.InternalServerError('Should redirect to tor: %s' % out_url)

        self.redirect(out_url)

    def write_file(self, filepath):
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
          raise errors.ResourceNotFound()

        mime_type, encoding = mimetypes.guess_type(filepath)
        if mime_type:
            self.set_header("Content-Type", mime_type)

        return StaticFileProducer(self, filepath).start()

    def force_file_download(self, filename, filepath):
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
          raise errors.ResourceNotFound()

        self.request.setHeader('X-Download-Options', 'noopen')
        self.request.setHeader('Content-Type', 'application/octet-stream')
        self.request.setHeader('Content-Disposition', 'attachment; filename=\"%s\"' % filename)

        return StaticFileProducer(self, filepath).start()

    @property
    def current_user(self):
        # Check for header based authentication
        session_id = self.request.headers.get('x-session')

        if session_id is None:
            return None

        return GLSessions.get(session_id)

    def should_redirect_tor(self):
        if GLSettings.onionservice is not None and self.client_using_tor:
            return True

        return False

    def should_redirect_https(self):
        if GLSettings.memory_copy.private.https_enabled and \
           self.client_ip not in GLSettings.local_hosts:
            return True
        else:
            return False

    def get_file_upload(self):
        try:
            chunk_size = len(self.request.args['file'][0])
            total_file_size = int(self.request.args['flowTotalSize'][0]) if 'flowTotalSize' in self.request.args else chunk_size
            flow_identifier = self.request.args['flowIdentifier'][0] if 'flowIdentifier' in self.request.args else generateRandomKey(10)

            if ((chunk_size / (1024 * 1024)) > GLSettings.memory_copy.maximum_filesize or
                (total_file_size / (1024 * 1024)) > GLSettings.memory_copy.maximum_filesize):
                log.err("File upload request rejected: file too big")
                raise errors.FileTooBig(GLSettings.memory_copy.maximum_filesize)

            if flow_identifier not in GLUploads:
                f = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
                GLUploads[flow_identifier] = f
            else:
                f = GLUploads[flow_identifier]

            f.write(self.request.args['file'][0])

            if 'flowChunkNumber' in self.request.args and 'flowTotalChunks' in self.request.args:
                if self.request.args['flowChunkNumber'][0] != self.request.args['flowTotalChunks'][0]:
                    return None

            mime_type, encoding = mimetypes.guess_type(self.request.args['flowFilename'][0])

            uploaded_file = {
                'name': self.request.args['flowFilename'][0],
                'type': mime_type,
                'size': total_file_size,
                'path': f.filepath,
                'body': f,
                'description': self.request.args.get('description', [''])[0]
            }

            return uploaded_file

        except errors.FileTooBig:
            raise  # propagate the exception

        except Exception as exc:
            log.err("Error while handling file upload %s" % exc)
            return None

    @inlineCallbacks
    def execution_check(self):
        self.request.execution_time = datetime.now() - self.request.start_time

        if self.request.execution_time.seconds > self.handler_exec_time_threshold:
            error = "Handler [%s] exceeded execution threshold (of %d secs) with an execution time of %.2f seconds" % \
                    (self.name, self.handler_exec_time_threshold, current_run_time)
            log.err(error)

            send_exception_email(error)

        track_handler(self)

        if self.uniform_answer_time:
            needed_delay = (GLSettings.side_channels_guard - (self.request.execution_time.microseconds / 1000)) / 1000
            if needed_delay > 0:
                yield deferred_sleep(needed_delay)



class StaticFileHandler(BaseHandler):
    check_roles = '*'

    def __init__(self, request, path):
        BaseHandler.__init__(self, request)

        self.root = "%s%s" % (os.path.abspath(path), "/")

    def write_file(self, filepath):
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
          raise errors.ResourceNotFound()

        mime_type, encoding = mimetypes.guess_type(filepath)
        if mime_type:
            self.request.setHeader(b'content-type', mime_type)

        return StaticFileProducer(self, filepath).start()

    def get(self, path):
        if path == '':
            path = 'index.html'

        abspath = os.path.abspath(os.path.join(self.root, path))

        directory_traversal_check(self.root, abspath)

        return self.write_file(abspath)
