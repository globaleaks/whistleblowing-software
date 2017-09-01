# -*- encoding: utf-8 -*-
import urlparse

from twisted.internet.address import IPv4Address
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.web.test.requesthelper import DummyRequest

from globaleaks.settings import GLSettings
from globaleaks.tests.helpers import TestGL


def forge_request(uri='https://www.globaleaks.org/', headers={}, method=b'GET', client_addr=None):
    """
    Creates a twisted.web.Request compliant request that is from an external
    IP address.
    """
    _, host, path, query, frag = urlparse.urlsplit(uri)

    x = host.split (':')
    if len(x) > 1:
        port = int(x[1])
    else:
        port = 80

    ret = DummyRequest([''])
    ret.method = method
    ret.uri = uri
    ret.path = path
    ret._serverName = bytes(host)

    if client_addr is None:
        ret.client = IPv4Address('TCP', '1.2.3.4', 12345)
    else:
        ret.client = client_addr

    def getHost():
        return IPv4Address('TCP', '127.0.0.1', port)

    ret.getHost = getHost

    def notifyFinish():
        return Deferred()

    ret.notifyFinish = notifyFinish

    for k, v in headers.items():
        ret.requestHeaders.setRawHeaders(bytes(k), [bytes(v)])

    ret.headers = ret.getAllHeaders()

    return ret


class TestAPI(TestGL):
    @inlineCallbacks
    def setUp(self):
        yield TestGL.setUp(self)

        from globaleaks.rest import api
        self.api = api.APIResourceWrapper()

    def test_api_spec(self):
        from globaleaks.rest import api
        for spec in api.api_spec:
            check_roles = getattr(spec[1], 'check_roles')
            self.assertIsNotNone(check_roles)

            if type(check_roles) == str:
                check_roles = {check_roles}

            self.assertTrue(len(check_roles) >= 1)
            self.assertTrue('*' not in check_roles or len(check_roles) == 1)
            self.assertTrue('unauthenticated' not in check_roles or len(check_roles) == 1)
            self.assertTrue('*' not in check_roles or len(check_roles) == 1)

            rest = filter(lambda a: a not in ['*',
                                              'unauthenticated',
                                              'whistleblower',
                                              'admin',
                                              'receiver',
                                              'custodian'], check_roles)
            self.assertTrue(len(rest) == 0)

    def test_get_with_no_language_header(self):
        request = forge_request()
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_get_with_gl_language_header(self):
        request = forge_request(headers={'GL-Language': 'it'})
        self.assertEqual(self.api.detect_language(request), 'it')

    def test_get_with_accept_language_header(self):
        request = forge_request(headers={'Accept-Language': 'ar;q=0.8,it;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'ar')

    def test_get_with_gl_language_header_and_accept_language_header_1(self):
        request = forge_request(headers={'GL-Language': 'en',
                                'Accept-Language': 'en-US,en;q=0.8,it;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_2(self):
        request = forge_request(headers={'GL-Language': 'antani',
                                'Accept-Language': 'en-US,en;it;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_3(self):
        request = forge_request(headers={'GL-Language': 'antani',
                                'Accept-Language': 'antani1,antani2;q=0.8,antani3;q=0.6'})
        self.assertEqual(self.api.detect_language(request), 'en')

    def test_status_codes_assigned(self):
        test_cases = [
            (b'GET', 200),
            (b'POST', 405),
            (b'PUT', 405),
            (b'DELETE', 405),
            (b'XXX', 405),
            (b'', 405),
        ]

        for meth, status_code in test_cases:
            request = forge_request(uri="https://www.globaleaks.org/", method=meth)
            self.api.render(request)
            self.assertEqual(request.responseCode, status_code)

    def test_request_state(self):
        url = "https://www.globaleaks.org/"
        request = forge_request(url)
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        request = forge_request(url, client_addr=IPv4Address('TCP', '127.0.0.1', 12345))
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        request = forge_request(uri='http://127.0.0.1:8083/', client_addr=IPv4Address('TCP', '127.0.0.1', 12345))
        self.api.render(request)
        self.assertTrue(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)


    def test_tor_detection(self):
        url = 'http://1234567890123456.onion/'

        GLSettings.memory_copy.onionservice = '1234567890123456.onion'
        GLSettings.appstate.tor_exit_set.add('1.2.3.4')

        request = forge_request(url)
        self.api.render(request)
        self.assertTrue(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        request = forge_request(url, client_addr=IPv4Address('TCP', '127.0.0.1', 12345))
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        GLSettings.appstate.tor_exit_set.clear()

    def test_tor_redirection(self):
        GLSettings.appstate.tor_exit_set.add('1.2.3.4')
        GLSettings.memory_copy.onionservice = '1234567890123456.onion'

        request = forge_request(uri="https://www.globaleaks.org/")

        self.api.render(request)
        self.assertTrue(request.client_using_tor)
        self.assertEqual(request.responseCode, 301)
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('http://1234567890123456.onion/', location)

        GLSettings.appstate.tor_exit_set.clear()

    def test_https_redirect(self):
        GLSettings.memory_copy.private.https_enabled = True
        GLSettings.memory_copy.hostname = 'www.globaleaks.org'

        request = forge_request(uri="https://www.globaleaks.org/", headers={'X-Tor2Web': '1'})
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 301)
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('https://www.globaleaks.org/', location)

        GLSettings.memory_copy.private.https_enabled = True
        GLSettings.memory_copy.hostname = 'www.globaleaks.org'
        request = forge_request(uri="http://www.globaleaks.org/public", headers={'X-Tor2Web': '1'})
        self.api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 301)
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('https://www.globaleaks.org/public', location)
