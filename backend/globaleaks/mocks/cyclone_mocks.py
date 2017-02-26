from StringIO import StringIO

from cyclone import httputil
from cyclone.escape import native_str, utf8
from cyclone.httpserver import HTTPConnection, HTTPRequest, _BadRequestException
from cyclone.web import RequestHandler

from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_now


def mock_RequestHandler_set_default_headers(self):
    """
    This mock is required to force some HTTP Headers on all
    the handlers included the internal error handlers of cyclone.
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
    self.set_header("Referrer-Policy", "no-referrer")

    # to avoid Robots spidering, indexing, caching
    if not GLSettings.memory_copy.allow_indexing:
        self.set_header("X-Robots-Tag", "noindex")

    # to mitigate clickjaking attacks on iframes allowing only same origin
    # same origin is needed in order to include svg and other html <object>
    if not GLSettings.memory_copy.allow_iframes_inclusion:
        self.set_header("X-Frame-Options", "sameorigin")

    if GLSettings.memory_copy.private.https_enabled:
        self.set_header('Strict-Transport-Security', 'max-age=31536000')


def mock_HTTPConnection_on_headers(self, data):
    """
    This mock is required to force size validation on all the handlers including 
    the internal cyclone handlers. The maximum request size is set to max_request_size.  
    NOTE that compatible frontends will only send 1/2 of that to the backend. 
    The extra space is for coushining multipart forms.
    """
    maximum_request_size = 2000 * 1024
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
            if content_length > maximum_request_size:
                raise _BadRequestException("Request exceeded size limit %d" % maximum_request_size)

            self._contentbuffer = StringIO()
            self.content_length = content_length
            self.setRawMode()
            return

        self.request_callback(self._request)
    except _BadRequestException as e:
        log.msg("Exception while handling HTTP request from %s: %s" % (self._remote_ip, e))
        self.transport.loseConnection()


def mock_HTTPConnection_on_request_body(self, data):
    """
    This mock is required to remove all the content parsing
    but 'multipart/form-data' on all handlers included the
    internal error handlers of cyclone.
    """
    self._request.body = data
    content_type = self._request.headers.get("Content-Type", "")
    if self._request.method in ("POST", "PATCH", "PUT"):
        if content_type.startswith("multipart/form-data"):
            fields = content_type.split(";")
            for field in fields:
                k, sep, v, = field.strip().partition("=")
                if k == "boundary" and v:
                    httputil.parse_multipart_form_data(
                        utf8(v), data,
                        self._request.arguments,
                        self._request.files)
                    break
            else:
                log.msg("Invalid multipart/form-data")

    self.request_callback(self._request)


RequestHandler.set_default_headers = mock_RequestHandler_set_default_headers
HTTPConnection._on_headers = mock_HTTPConnection_on_headers
HTTPConnection._on_request_body = mock_HTTPConnection_on_request_body
