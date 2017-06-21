import re
import urlparse

from twisted.internet.address import IPv4Address
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.web.test.requesthelper import DummyRequest

from globaleaks.settings import GLSettings
from globaleaks.tests.helpers import TestGL


def forge_request(uri='https://www.globaleaks.org/', headers={}, method=b'GET'):
    _, host, path, query, frag = urlparse.urlsplit(uri)

    ret = DummyRequest([''])
    ret.method = method
    ret.uri = uri
    ret.path = path
    ret._serverName = bytes(host)
    ret.client = IPv4Address('TCP', '1.2.3.4', 12345)

    def notifyFinish():
        return Deferred()

    ret.notifyFinish = notifyFinish

    for k, v in headers.iteritems():
        ret.requestHeaders.setRawHeaders(bytes(k), [bytes(v)])

    ret.headers = ret.getAllHeaders()

    return ret


def getAPI():
    from globaleaks.rest import api
    ret = api.APIResourceWrapper()

    return ret


class TestAPI(TestGL):
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
        api = getAPI()
        request = forge_request()
        self.assertEqual(api.detect_language(request), 'en')

    def test_get_with_gl_language_header(self):
        api = getAPI()
        request = forge_request(headers={'GL-Language': 'it'})
        self.assertEqual(api.detect_language(request), 'it')

    def test_get_with_accept_language_header(self):
        api = getAPI()
        request = forge_request(headers={'Accept-Language': 'ar;q=0.8,it;q=0.6'})
        self.assertEqual(api.detect_language(request), 'ar')

    def test_get_with_gl_language_header_and_accept_language_header_1(self):
        api = getAPI()
        request = forge_request(headers={'GL-Language': 'en',
                                'Accept-Language': 'en-US,en;q=0.8,it;q=0.6'})
        self.assertEqual(api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_2(self):
        api = getAPI()
        request = forge_request(headers={'GL-Language': 'antani',
                                'Accept-Language': 'en-US,en;it;q=0.6'})
        self.assertEqual(api.detect_language(request), 'en')

    def test_get_with_gl_language_header_and_accept_language_header_3(self):
        api = getAPI()
        request = forge_request(headers={'GL-Language': 'antani',
                                'Accept-Language': 'antani1,antani2;q=0.8,antani3;q=0.6'})
        self.assertEqual(api.detect_language(request), 'en')

    def test_status_codes_assigned(self):
        api = getAPI()

        test_cases = [
            (b'GET', 200),
            (b'POST', 405),
            (b'PUT', 405),
        ]

        for meth, status_code in test_cases:
            request = forge_request(uri="https://www.globaleaks.org/", method=meth)
            api.render(request)
            self.assertEqual(request.responseCode, status_code)

    def test_tor_and_https_redirect(self):
        api = getAPI()
        request = forge_request(uri="https://www.globaleaks.org/")
        api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        GLSettings.memory_copy.onionservice = '1234567890123456.onion'
        GLSettings.state.tor_exit_set.add('1.2.3.4')

        api = getAPI()
        request = forge_request('http://1234567890123456.onion/')
        api.render(request)
        self.assertTrue(request.client_using_tor)
        self.assertEqual(request.responseCode, 200)

        GLSettings.memory_copy.onionservice = '1234567890123456.onion'
        request = forge_request(uri="https://www.globaleaks.org/")
        api.render(request)
        self.assertTrue(request.client_using_tor)
        self.assertEqual(request.responseCode, 301)
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('http://1234567890123456.onion/', location)

        GLSettings.state.tor_exit_set.add('1.2.3.4')
        GLSettings.memory_copy.onionservice = '1234567890123456.onion'
        request = forge_request(uri="https://www.globaleaks.org/")
        api.render(request)
        self.assertTrue(request.client_using_tor)
        self.assertEqual(request.responseCode, 301)
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('http://1234567890123456.onion/', location)

        GLSettings.state.tor_exit_set.clear()

        api = getAPI()
        request = forge_request(uri="https://www.globaleaks.org/")
        api.render(request)
        self.assertEqual(request.responseCode, 200)

        GLSettings.memory_copy.private.https_enabled = True
        GLSettings.memory_copy.hostname = 'www.globaleaks.org'
        request = forge_request(uri="https://www.globaleaks.org/", headers={'X-Tor2Web': '1'})
        api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 301)
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('https://www.globaleaks.org/', location)

        GLSettings.memory_copy.private.https_enabled = True
        GLSettings.memory_copy.hostname = 'www.globaleaks.org'
        request = forge_request(uri="http://www.globaleaks.org/public", headers={'X-Tor2Web': '1'})
        api.render(request)
        self.assertFalse(request.client_using_tor)
        self.assertEqual(request.responseCode, 301)
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('https://www.globaleaks.org/public', location)
