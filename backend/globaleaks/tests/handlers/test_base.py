# -*- coding: utf-8 -*-
import json
from twisted.internet.defer import inlineCallbacks

from cyclone.web import HTTPError, HTTPAuthenticationRequired
from globaleaks.handlers.base import GLSession, GLSessions, BaseHandler, BaseStaticFileHandler, TimingStatsHandler
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers


FUTURE = 100


class BaseHandlerMock(BaseHandler):
    @BaseHandler.authenticated('admin')
    def get_authenticated(self):
        self.set_status(200)
        self.finish("test")

    @BaseHandler.unauthenticated
    def get_unauthenticated(self):
        self.set_status(200)
        self.finish("test")


class TestBaseHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = BaseHandlerMock

    @inlineCallbacks
    def test_successful_session_update_on_unauth_request(self):
        session = GLSession('admin', 'admin', 'enabled')
        date1 = session.getTime()
        self.test_reactor.pump([1] * FUTURE)
        handler = self.request({}, headers={'X-Session': session.id})
        yield handler.get_unauthenticated()
        date2 = GLSessions.get(session.id).getTime()
        self.assertEqual(date1 + FUTURE, date2)

    @inlineCallbacks
    def test_successful_session_update_on_auth_request(self):
        session = GLSession('admin', 'admin', 'enabled')
        date1 = session.getTime()
        self.test_reactor.pump([1] * FUTURE)
        handler = self.request({}, headers={'X-Session': session.id})
        yield handler.get_authenticated()
        date2 = GLSessions.get(session.id).getTime()
        self.assertEqual(date1 + FUTURE, date2)

    @inlineCallbacks
    def test_base_handler_on_finish(self):
        handler = self.request({})
        yield handler.get_unauthenticated()
        handler.on_finish()

    @inlineCallbacks
    def test_basic_auth_on_and_valid_authentication(self):
        GLSettings.memory_copy.basic_auth = True
        GLSettings.memory_copy.basic_auth_username = 'globaleaks'
        GLSettings.memory_copy.basic_auth_password = 'globaleaks'
        handler = self.request({}, headers={'Authorization': 'Basic Z2xvYmFsZWFrczpnbG9iYWxlYWtz'})
        yield handler.get_unauthenticated()

    def test_basic_auth_on_and_invalid_authentication(self):
        GLSettings.memory_copy.basic_auth = True
        GLSettings.memory_copy.basic_auth_username = 'globaleaks'
        GLSettings.memory_copy.basic_auth_password = 'globaleaks'
        handler = self.request({}, headers={'Authorization': 'Basic Z2xvYmFsZWFrczp3cm9uZ3Bhc3N3b3Jk'})
        self.assertRaises(HTTPAuthenticationRequired, handler.get_unauthenticated)

    def test_basic_auth_on_and_missing_authentication(self):
        GLSettings.memory_copy.basic_auth = True
        GLSettings.memory_copy.basic_auth_username = 'globaleaks'
        GLSettings.memory_copy.basic_auth_password = 'globaleaks'
        handler = self.request({})
        self.assertRaises(HTTPAuthenticationRequired, handler.get_unauthenticated)

    @inlineCallbacks
    def test_get_with_no_language_header(self):
        handler = self.request({})
        yield handler.get_unauthenticated()
        self.assertEqual(handler.request.language, 'en')

    @inlineCallbacks
    def test_get_with_gl_language_header(self):
        handler = self.request({}, headers={'GL-Language': 'it'})
        yield handler.get_unauthenticated()
        self.assertEqual(handler.request.language, 'it')

    @inlineCallbacks
    def test_get_with_accept_language_header(self):
        handler = self.request({}, headers={'Accept-Language': 'ar;q=0.8,it;q=0.6'})
        yield handler.get_unauthenticated()
        self.assertEqual(handler.request.language, 'ar')

    @inlineCallbacks
    def test_get_with_gl_language_header_and_accept_language_header_1(self):
        handler = self.request({}, headers={'GL-Language': 'en',
                                            'Accept-Language': 'en-US,en;q=0.8,it;q=0.6'})
        yield handler.get_unauthenticated()
        self.assertEqual(handler.request.language, 'en')

    @inlineCallbacks
    def test_get_with_gl_language_header_and_accept_language_header_2(self):
        handler = self.request({}, headers={'GL-Language': 'antani',
                                            'Accept-Language': 'en-US,en;it;q=0.6'})
        yield handler.get_unauthenticated()
        self.assertEqual(handler.request.language, 'en')

    @inlineCallbacks
    def test_get_with_gl_language_header_and_accept_language_header_3(self):
        handler = self.request({}, headers={'GL-Language': 'antani',
                                            'Accept-Language': 'antani1,antani2;q=0.8,antani3;q=0.6'})
        yield handler.get_unauthenticated()
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

    def test_validate_host(self):
        self.assertFalse(BaseHandler.validate_host(""))
        self.assertTrue(BaseHandler.validate_host("127.0.0.1"))
        self.assertTrue(BaseHandler.validate_host("thirteenchars123.onion"))
        self.assertTrue(BaseHandler.validate_host("thirteenchars123.onion:31337"))
        self.assertFalse(BaseHandler.validate_host("invalid.onion"))
        self.assertFalse(BaseHandler.validate_host("invalid.onion:12345"))  # gabanbus i miss you!


class TestBaseStaticFileHandler(helpers.TestHandler):
    _handler = BaseStaticFileHandler

    @inlineCallbacks
    def test_get_existent(self):
        handler = self.request(kwargs={'path': GLSettings.client_path})
        yield handler.get('')
        self.assertEqual(handler.get_status(), 200)

    @inlineCallbacks
    def test_get_unexistent(self):
        handler = self.request(kwargs={'path': GLSettings.client_path})
        yield self.assertFailure(handler.get('unexistent'), HTTPError)


class TestTimingStats(helpers.TestHandler):
    _handler = TimingStatsHandler

    @inlineCallbacks
    def setUp(self):
        yield super(TestTimingStats, self).setUp()
        TimingStatsHandler.TimingsTracker = []

    @inlineCallbacks
    def test_get_feature_disabled(self):
        GLSettings.log_timing_stats = False

        TimingStatsHandler.log_measured_timing("JOB", "Session Management", 1443252274.44, 0)
        TimingStatsHandler.log_measured_timing("GET", "/styles/main.css", 1443252277.68, 0)

        handler = self.request()

        yield handler.get()

        splits = self.responses[0].split("\n")

        self.assertEqual(len(splits), 2)

        self.assertEqual(splits[0], "category,method,uri,start_time,run_time")
        self.assertEqual(splits[1], "")

    @inlineCallbacks
    def test_get_feature_enabled(self):
        GLSettings.log_timing_stats = True

        TimingStatsHandler.log_measured_timing("JOB", "Session Management", 1443252274.44, 0)
        TimingStatsHandler.log_measured_timing("GET", "/styles/main.css", 1443252277.68, 0)
        TimingStatsHandler.log_measured_timing("JOB", "Delivery", 1443252279.0, 0)
        TimingStatsHandler.log_measured_timing("POST", "/token", 1443252280.0, 0)
        TimingStatsHandler.log_measured_timing("PUT", "/submission/XXA82cSXFHTOoVroWlOGqg2VF8XtJQ57QIYM09YanY", 1443252281.0, 0)
        TimingStatsHandler.log_measured_timing("POST", "/wbtip/comments", 1443252282.0, 0)
        handler = self.request()

        yield handler.get()

        splits = self.responses[0].split("\n")

        self.assertEqual(len(splits), 8)

        self.assertEqual(splits[0], "category,method,uri,start_time,run_time")
        self.assertEqual(splits[1], "uncategorized,JOB,Session Management,1443252274.44,0")
        self.assertEqual(splits[2], "uncategorized,GET,/styles/main.css,1443252277.68,0")
        self.assertEqual(splits[3], "delivery,JOB,Delivery,1443252279.0,0")
        self.assertEqual(splits[4], "token,POST,/token,1443252280.0,0")
        self.assertEqual(splits[5], "submission,PUT,/submission/XXA82cSXFHTOoVroWlOGqg2VF8XtJQ57QIYM09YanY,1443252281.0,0")
        self.assertEqual(splits[6], "comment,POST,/wbtip/comments,1443252282.0,0")
        self.assertEqual(splits[7], "")

    @inlineCallbacks
    def test_get_feature_enabled_discard_timingstatss_handler_logging(self):
        GLSettings.log_timing_stats = True

        TimingStatsHandler.log_measured_timing("GET", "/s/timings", 1443252274.44, 0)

        handler = self.request()

        yield handler.get()

        splits = self.responses[0].split("\n")

        self.assertEqual(len(splits), 2)

        self.assertEqual(splits[0], "category,method,uri,start_time,run_time")
        self.assertEqual(splits[1], "")
