# -*- coding: utf-8 -*-
from twisted.internet.address import IPv4Address
from twisted.internet.defer import inlineCallbacks

from globaleaks.db import refresh_memory_variables
from globaleaks.handlers.admin.node import db_update_enabled_languages
from globaleaks.orm import tw
from globaleaks.rest import api
from globaleaks.state import State
from globaleaks.tests.helpers import TestGL, forge_request


class TestAPI(TestGL):
    @inlineCallbacks
    def setUp(self):
        yield TestGL.setUp(self)

        self.api = api.APIResourceWrapper()

        yield tw(db_update_enabled_languages, 1, ['en', 'ar', 'it'], 'en')
        yield refresh_memory_variables()

    def test_api_spec(self):
        for spec in api.api_spec:
            check_roles = getattr(spec[1], 'check_roles')
            self.assertIsNotNone(check_roles)

            if isinstance(check_roles, str):
                check_roles = {check_roles}

            self.assertTrue(len(check_roles) >= 1)
            self.assertTrue('any' not in check_roles or len(check_roles) == 1)

            rest = list(filter(lambda a: a not in ['any',
                                                   'user',
                                                   'whistleblower',
                                                   'admin',
                                                   'receiver',
                                                   'custodian'], check_roles))
            self.assertTrue(len(rest) == 0)

    def test_get_with_no_language_header(self):
        request = forge_request()
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_get_with_gl_language_header(self):
        request = forge_request(headers={'Accept-Language': 'it'})
        self.assertEqual(self.api.detect_language(request), 'it')

    def test_get_with_accept_language_header(self):
        request = forge_request(headers={'Accept-Language': 'ar;q=0.8,it;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'ar')

    def test_get_with_gl_language_header_and_accept_language_header_1(self):
        request = forge_request(headers={'Accept-Language': 'en-US,en;q=0.8,it;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_2(self):
        request = forge_request(headers={'Accept-Language': 'en-US,en;it;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_3(self):
        request = forge_request(headers={'Accept-Language': 'antani1,antani2;q=0.8,antani3;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_status_codes_assigned(self):
        test_cases = [
            (b'', 501),
            (b'DELETE', 501),
            (b'GET', 200),
            (b'HEAD', 200),
            (b'OPTIONS', 200),
            (b'POST', 501),
            (b'PUT', 501),
            (b'XXX', 501)
        ]

        server_headers = [
            ('Cache-control', 'no-store'),
            ('Content-Language', 'en'),
            ('Content-Security-Policy', 'base-uri \'none\';' \
                                        'default-src \'none\';' \
                                        'connect-src \'self\';' \
                                        'style-src \'self\' \'sha256-fwyo2zCGlh85NfN4rQUlpLM7MB5cry/1AEDA/G9mQJ8=\';' \
                                        'script-src \'self\' \'sha256-IYBZitj/YWbzjFFnwLPjJJmMGdSj923kzu2tdCxLKdU=\';' \
                                        'img-src \'self\' data:;' \
                                        'font-src \'self\' data:;' \
                                        'media-src \'self\';' \
                                        'form-action \'self\';' \
                                        'block-all-mixed-content;' \
                                        'frame-ancestors \'none\';'),
            ('Permissions-Policy', "camera=()," \
                                   "document-domain=()," \
                                   "fullscreen=()," \
                                   "geolocation=()," \
                                   "microphone=()"),
            ('Referrer-Policy', 'no-referrer'),
            ('Server', 'GlobaLeaks'),
            ('X-Content-Type-Options', 'nosniff'),
            ('X-Check-Tor', 'False'),
            ('X-Frame-Options', 'deny'),
            ('X-XSS-Protection', '1; mode=block'),
        ]

        for method, status_code in test_cases:
            request = forge_request(uri=b"https://www.globaleaks.org/", method=method)
            self.api.render(request)
            self.assertEqual(request.responseCode, status_code)
            for headerName, expectedHeaderValue in server_headers:
                returnedHeaderValue = request.responseHeaders.getRawHeaders(headerName)[0]
                self.assertEqual(returnedHeaderValue, expectedHeaderValue)

    def test_request_state_and_redirects(self):
        # Remote HTTP connection with HTTPS disabled
        request = forge_request(uri=b'http://www.globaleaks.org/')
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        # Local HTTP connection on port 8082 should be marked as not coming from Tor
        request = forge_request(uri=b'http://127.0.0.1:8082/', client_addr=IPv4Address('TCP', '127.0.0.1', 12345))
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        # Local HTTP connection on port 8083 should be marked as coming from Tor
        request = forge_request(uri=b'http://127.0.0.1:8083/', client_addr=IPv4Address('TCP', '127.0.0.1', 12345))
        self.api.render(request)
        self.assertTrue(request.client_using_tor)
        self.assertEqual(request.responseCode, 302)

        # Remote HTTP connection not coming from Tor should be redirected to HTTPS
        State.tenant_cache[1].https_enabled = True
        request = forge_request(uri=b'http://www.globaleaks.org/public', client_addr=IPv4Address('TCP', '8.8.8.8', 12345))
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 302)
        self.assertEqual(request.responseHeaders.getRawHeaders('location')[0], 'https://www.globaleaks.org/public')
        State.tenant_cache[1].https_enabled = False
