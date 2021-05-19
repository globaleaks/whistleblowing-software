# -*- coding: utf-8 -*-
import collections
import json
import mimetypes
import os
import re

from datetime import datetime

from twisted.internet import abstract
from twisted.protocols.basic import FileSender

from globaleaks.event import track_handler
from globaleaks.rest import errors, requests
from globaleaks.sessions import Sessions
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.ip import check_ip
from globaleaks.utils.log import log
from globaleaks.utils.securetempfile import SecureTemporaryFile
from globaleaks.utils.utility import datetime_now, deferred_sleep

# https://github.com/globaleaks/GlobaLeaks/issues/1601
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
mimetypes.add_type('application/x-font-ttf', '.ttf')
mimetypes.add_type('application/woff', '.woff')
mimetypes.add_type('application/woff2', '.woff2')


def serve_file(request, fo):
    def on_finish(ignored):
        fo.close()
        request.finish()

    filesender = FileSender().beginFileTransfer(fo, request)

    filesender.addBoth(on_finish)

    return filesender



def connection_check(tid, client_ip, role, client_using_tor):
    """
    Accept or refuse a connection in relation to the platform settings

    :param tid: A tenant ID
    :param client_ip: A client IP
    :param role: A user role
    :param client_using_tor: A boolean for signaling Tor use
    """
    ip_filter = State.tenant_cache[tid]['ip_filter'].get(role)
    if ip_filter and not check_ip(client_ip, ip_filter):
        raise errors.AccessLocationInvalid

    https_allowed = State.tenant_cache[tid]['https_allowed'].get(role)
    if not https_allowed and not client_using_tor:
        raise errors.TorNetworkRequired


class BaseHandler(object):
    check_roles = 'admin'
    require_token = []
    handler_exec_time_threshold = 120
    uniform_answer_time = False
    cache_resource = False
    invalidate_cache = False
    root_tenant_only = False
    upload_handler = False
    uploaded_file = None
    refresh_connection_endpoints = False

    def __init__(self, state, request):
        self.name = type(self).__name__
        self.state = state
        self.request = request
        self.request.start_time = datetime.now()
        self.token = False
        self.session = self.get_session()

    def get_session(self):
        if hasattr(self, 'session'):
            return self.session

        # Check session header
        session_id = self.request.headers.get(b'x-session')

        # Check token GET argument:
        if b'token' in self.request.args:
            try:
                token_id = self.request.args[b'token'][0].decode()
                self.token = self.state.tokens.validate(token_id)
                if self.token.session is not None:
                    session_id = self.token.session.id.encode()
            except:
                raise errors.InternalServerError("TokenFailure: Invalid")

        if session_id is None:
            return

        session = Sessions.get(session_id.decode())

        if session is None or session.tid != self.request.tid:
            return

        self.session = session

        if self.session.user_role != 'whistleblower' and \
           self.state.tenant_cache[1].get('log_accesses_of_internal_users', False):
           self.request.log_ip_and_ua = True

        return self.session

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
            except:
                return False

        if python_type == bool:
            if value == 'true' or value == 'false':
                return True

        return isinstance(value, python_type)

    @staticmethod
    def validate_regexp(value, type):
        """
        Return True if the python class matches the given regexp.
        """
        return bool(re.match(type, value))

    @staticmethod
    def validate_type(value, type):
        retval = False

        if value is None:
            log.err("-- Invalid python_type, in [%s] expected %s", value, type)

        # if it's callable, than assumes is a primitive class
        elif callable(type):
            retval = BaseHandler.validate_python_type(value, type)
            if not retval:
                log.err("-- Invalid python_type, in [%s] expected %s", value, type)

        # value as "{foo:bar}"
        elif isinstance(type, collections.Mapping):
            retval = BaseHandler.validate_jmessage(value, type)
            if not retval:
                log.err("-- Invalid JSON/dict [%s] expected %s", value, type)

        # regexp
        elif isinstance(type, str):
            retval = BaseHandler.validate_regexp(value, type)
            if not retval:
                log.err("-- Failed Match in regexp [%s] against %s", value, type)

        # value as "[ type ]"
        elif isinstance(type, collections.Iterable):
            # empty list is ok
            if not value:
                retval = True

            else:
                retval = all(BaseHandler.validate_type(x, type[0]) for x in value)
                if not retval:
                    log.err("-- List validation failed [%s] of %s", value, type)

        return retval

    @staticmethod
    def validate_jmessage(jmessage, message_template):
        """
        Takes a string that represents a JSON messages and checks to see if it
        conforms to the message type it is supposed to be.

        This message must be either a dict or a list. This function may be called
        recursively to validate sub-parameters that are also go GLType.
        """
        if isinstance(message_template, dict):
            success_check = 0
            keys_to_strip = []
            for key, value in jmessage.items():
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
                    log.err("Received key %s: type validation fail", key)
                    raise errors.InputValidationError("Key (%s) type validation failure" % key)
                success_check += 1

            for key in keys_to_strip:
                del jmessage[key]

            for key, value in message_template.items():
                if key not in jmessage:
                    log.debug("Key %s expected but missing!", key)
                    log.debug("Received schema %s - Expected %s",
                              jmessage.keys(), message_template.keys())
                    raise errors.InputValidationError("Missing key %s" % key)

                if not BaseHandler.validate_type(jmessage[key], value):
                    log.err("Expected key: %s type validation failure", key)
                    raise errors.InputValidationError("Key (%s) double validation failure" % key)

                if isinstance(message_template[key], (dict, list)) and message_template[key]:
                    BaseHandler.validate_jmessage(jmessage[key], message_template[key])

                success_check += 1

            if success_check != len(message_template) * 2:
                log.err("Success counter double check failure: %d", success_check)
                raise errors.InputValidationError("Success counter double check failure")

            return True

        elif isinstance(message_template, list):
            if not all(BaseHandler.validate_type(x, message_template[0]) for x in jmessage):
                raise errors.InputValidationError("Not every element in %s is %s" %
                                                  (jmessage, message_template[0]))
            return True

        else:
            raise errors.InputValidationError("invalid json massage: expected dict or list")

    @staticmethod
    def validate_message(message, message_template):
        try:
            jmessage = json.loads(message)
        except ValueError:
            raise errors.InputValidationError("Invalid JSON format")

        if BaseHandler.validate_jmessage(jmessage, message_template):
            return jmessage

        raise errors.InputValidationError("Unexpected condition!?")

    def redirect(self, url):
        self.request.setResponseCode(301)
        self.request.setHeader(b'location', url)

    def check_file_presence(self, filepath):
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            raise errors.ResourceNotFound()

    def open_file(self, filepath):
        self.check_file_presence(filepath)

        return open(filepath, 'rb')

    def write_file(self, filename, fp):
        if isinstance(fp, str):
            fp = self.open_file(fp)

        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            self.request.setHeader(b'Content-Type', mime_type)

        return serve_file(self.request, fp)

    def write_file_as_download(self, filename, fp):
        if isinstance(fp, str):
            fp = self.open_file(fp)

        self.request.setHeader(b'X-Download-Options', b'noopen')
        self.request.setHeader(b'Content-Type', b'application/octet-stream')
        self.request.setHeader(b'Content-Disposition',
                               'attachment; filename="%s"' % filename)

        return serve_file(self.request, fp)

    def process_file_upload(self):
        if b'flowFilename' not in self.request.args:
            return

        total_file_size = int(self.request.args[b'flowTotalSize'][0])
        file_id = self.request.args[b'flowIdentifier'][0].decode()

        chunk_size = len(self.request.args[b'file'][0])
        if ((chunk_size // (1024 * 1024)) > self.state.tenant_cache[self.request.tid].maximum_filesize or
            (total_file_size // (1024 * 1024)) > self.state.tenant_cache[self.request.tid].maximum_filesize):
            log.err("File upload request rejected: file too big", tid=self.request.tid)
            raise errors.FileTooBig(self.state.tenant_cache[self.request.tid].maximum_filesize)

        if file_id not in self.state.TempUploadFiles:
            self.state.TempUploadFiles[file_id] = SecureTemporaryFile(Settings.tmp_path)

        f = self.state.TempUploadFiles[file_id]
        with f.open('w') as f:
            f.write(self.request.args[b'file'][0])

            if self.request.args[b'flowChunkNumber'][0] != self.request.args[b'flowTotalChunks'][0]:
                return None

            f.finalize_write()

        mime_type, _ = mimetypes.guess_type(self.request.args[b'flowFilename'][0].decode())
        if mime_type is None:
            mime_type = 'application/octet-stream'

        filename = self.request.args[b'flowFilename'][0].decode()

        self.uploaded_file = {
            'id': file_id,
            'date': datetime_now(),
            'name': filename,
            'type': mime_type,
            'size': total_file_size,
            'filename': os.path.basename(f.filepath),
            'body': f,
            'description': self.request.args.get(b'description', [''])[0]
        }

    def write_upload_plaintext_to_disk(self, destination):
        """
        :param destination: the path where to store the file
        :return: a descriptor dictionary for the saved file
        """
        try:
            log.debug('Creating file %s with %d bytes', destination, self.uploaded_file['size'])

            with self.uploaded_file['body'].open('r') as encrypted_file, open(destination, 'wb') as plaintext_file:
                while True:
                    chunk = encrypted_file.read(abstract.FileDescriptor.bufferSize)
                    if not chunk:
                        break

                    plaintext_file.write(chunk)

        finally:
            self.uploaded_file['path'] = destination

    def execution_check(self):
        self.request.execution_time = datetime.now() - self.request.start_time

        if self.request.execution_time.seconds > self.handler_exec_time_threshold:
            err_tup = ("Handler [%s] exceeded execution threshold (of %d secs) with an execution time of %.2f seconds",
                       self.name, self.handler_exec_time_threshold, self.request.execution_time.seconds)
            log.err(tid=self.request.tid, *err_tup)
            self.state.schedule_exception_email(self.request.tid, *err_tup)

        track_handler(self)

        if self.uniform_answer_time:
            needed_delay = (float(Settings.side_channels_guard) - (float(self.request.execution_time.microseconds) / float(1000))) / float(1000)
            if needed_delay > 0:
                return deferred_sleep(needed_delay)
