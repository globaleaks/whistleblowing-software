# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import GLSession, GLSessions, BaseHandler, StaticFileHandler
from globaleaks.rest.errors import InvalidInputFormat, ResourceNotFound
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers

FUTURE = 100


class BaseHandlerMock(BaseHandler):
    check_roles = 'unauthenticated'

    def get(self):
        return

class TestBaseHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = BaseHandlerMock

    @inlineCallbacks
    def test_get_with_no_language_header(self):
        handler = self.request({})
        yield handler.get()
        self.assertEqual(handler.request.language, 'en')

    @inlineCallbacks
    def test_get_with_gl_language_header(self):
        handler = self.request({}, headers={'GL-Language': 'it'})
        yield handler.get()
        self.assertEqual(handler.request.language, 'it')

    @inlineCallbacks
    def test_get_with_accept_language_header(self):
        handler = self.request({}, headers={'Accept-Language': 'ar;q=0.8,it;q=0.6'})
        yield handler.get()
        self.assertEqual(handler.request.language, 'ar')

    @inlineCallbacks
    def test_get_with_gl_language_header_and_accept_language_header_1(self):
        handler = self.request({}, headers={'GL-Language': 'en',
                                            'Accept-Language': 'en-US,en;q=0.8,it;q=0.6'})
        yield handler.get()
        self.assertEqual(handler.request.language, 'en')

    @inlineCallbacks
    def test_get_with_gl_language_header_and_accept_language_header_2(self):
        handler = self.request({}, headers={'GL-Language': 'antani',
                                            'Accept-Language': 'en-US,en;it;q=0.6'})
        yield handler.get()
        self.assertEqual(handler.request.language, 'en')

    @inlineCallbacks
    def test_get_with_gl_language_header_and_accept_language_header_3(self):
        handler = self.request({}, headers={'GL-Language': 'antani',
                                            'Accept-Language': 'antani1,antani2;q=0.8,antani3;q=0.6'})
        yield handler.get()
        self.assertEqual(handler.request.language, 'en')

    def test_validate_jmessage_valid(self):
        dummy_message = {'spam': 'ham', 'firstd': {3: 4}, 'fields': "CIAOCIAO", 'nest': [{1: 2, 3: 4}]}
        dummy_message_template = {'spam': str, 'firstd': dict, 'fields': '\w+', 'nest': [dict]}

        self.assertTrue(BaseHandler.validate_jmessage(dummy_message, dummy_message_template))

    def test_validate_jmessage_invalid(self):
        dummy_message = {}
        dummy_message_template = {'spam': str, 'firstd': dict, 'fields': '\w+', 'nest': [dict]}

        self.assertRaises(InvalidInputFormat,
                          BaseHandler.validate_jmessage, dummy_message, dummy_message_template)

    def test_validate_message_valid(self):
        dummy_json = json.dumps({'spam': 'ham'})
        dummy_message_template = {'spam': unicode}

        self.assertEqual(json.loads(dummy_json), BaseHandler.validate_message(dummy_json, dummy_message_template))

    def test_validate_message_invalid(self):
        dummy_json = json.dumps({'spam': 'ham'})
        dummy_message_template = {'spam': dict}

        self.assertRaises(InvalidInputFormat,
                          BaseHandler.validate_message, dummy_json, dummy_message_template)

    def test_validate_type_valid(self):
        self.assertTrue(BaseHandler.validate_type('foca', str))
        self.assertTrue(BaseHandler.validate_type(True, bool))
        self.assertTrue(BaseHandler.validate_type(4, int))
        self.assertTrue(BaseHandler.validate_type(u'foca', unicode))
        self.assertTrue(BaseHandler.validate_type(['foca', 'fessa'], list))
        self.assertTrue(BaseHandler.validate_type({'foca': 1}, dict))

    def test_validate_type_invalid(self):
        self.assertFalse(BaseHandler.validate_type(1, str))
        self.assertFalse(BaseHandler.validate_type(1, unicode))
        self.assertFalse(BaseHandler.validate_type(False, unicode))
        self.assertFalse(BaseHandler.validate_type({}, list))
        self.assertFalse(BaseHandler.validate_type(True, dict))

    def test_validate_python_type_valid(self):
        self.assertTrue(BaseHandler.validate_python_type('foca', str))
        self.assertTrue(BaseHandler.validate_python_type(True, bool))
        self.assertTrue(BaseHandler.validate_python_type(4, int))
        self.assertTrue(BaseHandler.validate_python_type(u'foca', unicode))
        self.assertTrue(BaseHandler.validate_python_type(None, dict))

    def test_validate_regexp_valid(self):
        self.assertTrue(BaseHandler.validate_regexp('Foca', '\w+'))
        self.assertFalse(BaseHandler.validate_regexp('Foca', '\d+'))

    @inlineCallbacks
    def test_client_using_tor(self):
        handler = self.request({}, headers={})
        yield handler.get()
        self.assertFalse(handler.client_using_tor)

        GLSettings.state.tor_exit_set.add('1.2.3.4')

        handler = self.request({}, headers={})
        yield handler.get()
        self.assertTrue(handler.client_using_tor)

        # Now test if the Tor2Web catching logic does its job.
        handler = self.request({}, headers={'X-Tor2Web': '1'})
        yield handler.get()
        self.assertFalse(handler.client_using_tor)


class TestStaticFileHandler(helpers.TestHandler):
    _handler = StaticFileHandler

    @inlineCallbacks
    def test_get_existent(self):
        handler = self.request(kwargs={'path': GLSettings.client_path})
        yield handler.get('')
        self.assertEqual(handler.get_status(), 200)

    @inlineCallbacks
    def test_get_unexistent(self):
        handler = self.request(kwargs={'path': GLSettings.client_path})

        try:
            yield handler.get('unexistent')
        except ResourceNotFound:
            return

        self.fail('should throw resource not found error')
