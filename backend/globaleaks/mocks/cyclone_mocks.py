from StringIO import StringIO

from cyclone import httputil
from cyclone.escape import native_str
from cyclone.httpserver import HTTPConnection, HTTPRequest, _BadRequestException
from cyclone.web import RequestHandler

from globaleaks.security import GLSecureTemporaryFile
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import datetime_now


def mock_RequestHandler_set_default_headers(self):
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

    self.set_header("Cache-control", "no-cache, no-store, must-revalidate")
    self.set_header("Pragma", "no-cache")

    self.set_header("Expires", "-1")

    # to avoid information leakage via referrer
    self.set_header("Content-Security-Policy", "referrer no-referrer")

    # to avoid Robots spidering, indexing, caching
    if not GLSettings.memory_copy.allow_indexing:
        self.set_header("X-Robots-Tag", "noindex")

    # to mitigate clickjaking attacks on iframes allowing only same origin
    # same origin is needed in order to include svg and other html <object>
    if not GLSettings.memory_copy.allow_iframes_inclusion:
        self.set_header("X-Frame-Options", "sameorigin")


def mock_HTTPConnection_on_headers(self, data):
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

RequestHandler.set_default_headers = mock_RequestHandler_set_default_headers
HTTPConnection._on_headers = mock_HTTPConnection_on_headers
