import json
from datetime import datetime
from mock import Mock

from twisted.trial import unittest
from twisted.internet import defer
from twisted.python.failure import Failure
from twisted.web.client import ResponseDone

from txtorcon.router import Router, hexIdFromHash, hashFromHexId


class FakeController(object):
    def get_info_raw(self, i):
        return defer.succeed('250-ip-to-country/something=XX\r\n250 OK')


class UtilityTests(unittest.TestCase):

    def test_hex_converters(self):
        self.assertEqual(
            hexIdFromHash('AHhuQ8zFQJdT8l42Axxc6m6kNwI'),
            '$00786E43CCC5409753F25E36031C5CEA6EA43702'
        )
        self.assertEqual(
            hashFromHexId('$00786E43CCC5409753F25E36031C5CEA6EA43702'),
            'AHhuQ8zFQJdT8l42Axxc6m6kNwI'
        )
        # should work with or without leading $
        self.assertEqual(
            hexIdFromHash(hashFromHexId('00786E43CCC5409753F25E36031C5CEA6EA43702')),
            '$00786E43CCC5409753F25E36031C5CEA6EA43702'
        )


class RouterTests(unittest.TestCase):

    def test_ctor(self):
        controller = object()
        router = Router(controller)
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "77.183.225.114",
                      "24051", "24052")
        self.assertEqual(
            router.id_hex,
            "$00786E43CCC5409753F25E36031C5CEA6EA43702"
        )

        # we assert this twice to cover the cached + uncached cases
        self.assertTrue(isinstance(router.modified, datetime))
        self.assertTrue(isinstance(router.modified, datetime))
        self.assertEqual(router.policy, '')

    def test_unique_name(self):
        controller = object()
        router = Router(controller)
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "77.183.225.114",
                      "24051", "24052")
        self.assertEqual(
            router.id_hex,
            "$00786E43CCC5409753F25E36031C5CEA6EA43702"
        )
        self.assertEqual(
            router.unique_name,
            "$00786E43CCC5409753F25E36031C5CEA6EA43702"
        )
        router.flags = ['Named']
        self.assertEqual(router.unique_name, "foo")

    def test_flags(self):
        controller = object()
        router = Router(controller)
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "77.183.225.114",
                      "24051", "24052")
        router.flags = "Exit Fast Named Running V2Dir Valid".split()
        self.assertEqual(router.name_is_unique, True)

    def test_flags_from_string(self):
        controller = object()
        router = Router(controller)
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "77.183.225.114",
                      "24051", "24052")
        router.flags = "Exit Fast Named Running V2Dir Valid"
        self.assertEqual(router.name_is_unique, True)

    def test_policy_accept(self):
        controller = object()
        router = Router(controller)
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "77.183.225.114",
                      "24051", "24052")
        router.policy = "accept 25,128-256".split()
        self.assertTrue(router.accepts_port(25))
        for x in range(128, 256):
            self.assertTrue(router.accepts_port(x))
        self.assertTrue(not router.accepts_port(26))
        self.assertEqual(router.policy, 'accept 25,128-256')

    def test_policy_reject(self):
        controller = object()
        router = Router(controller)
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "77.183.225.114",
                      "24051", "24052")
        router.policy = "reject 500-600,655,7766".split()
        for x in range(1, 500):
            self.assertTrue(router.accepts_port(x))
        for x in range(500, 601):
            self.assertTrue(not router.accepts_port(x))

        self.assertEqual(router.policy, 'reject 500-600,655,7766')

    def test_countrycode(self):
        class CountryCodeController(object):
            def get_info_raw(self, i):
                return defer.succeed(
                    '250-ip-to-country/127.1.2.3=ZZ\r\n250 OK'
                )
        controller = CountryCodeController()
        router = Router(controller)
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "127.1.2.3",
                      "24051", "24052")

        self.assertEqual(router.location.countrycode, 'ZZ')

    def test_policy_error(self):
        router = Router(object())
        try:
            router.policy = 'foo 123'
            self.fail()
        except Exception as e:
            self.assertTrue("Don't understand" in str(e))

    def test_policy_not_set_error(self):
        router = Router(object())
        try:
            router.accepts_port(123)
            self.fail()
        except Exception as e:
            self.assertTrue("policy" in str(e))

    def test_repr(self):
        router = Router(FakeController())
        router.update("foo",
                      "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
                      "MAANkj30tnFvmoh7FsjVFr+cmcs",
                      "2011-12-16 15:11:34",
                      "1.2.3.4",
                      "24051", "24052")
        router.flags = ['Named']
        repr(router)

    def test_repr_no_update(self):
        router = Router(FakeController())
        repr(router)


class OnionOOTests(unittest.TestCase):

    def setUp(self):
        self.router = Router(FakeController())
        self.router.update(
            "foo",
            "AHhuQ8zFQJdT8l42Axxc6m6kNwI",
            "MAANkj30tnFvmoh7FsjVFr+cmcs",
            "2011-12-16 15:11:34",
            "1.2.3.4",
            "24051", "24052"
        )

    @defer.inlineCallbacks
    def test_onionoo_get_fails(self):
        agent = Mock()
        resp = Mock()
        resp.code = 500
        agent.request = Mock(return_value=defer.succeed(resp))

        with self.assertRaises(Exception) as ctx:
            yield self.router.get_onionoo_details(agent)
        self.assertTrue(
            "Failed to lookup" in str(ctx.exception)
        )

    @defer.inlineCallbacks
    def test_onionoo_success(self):
        agent = Mock()
        resp = Mock()
        resp.code = 200

        def feed_response(protocol):
            config = {
                "relays": [
                    {
                        "fingerprint": "00786E43CCC5409753F25E36031C5CEA6EA43702",
                    },
                ]
            }
            protocol.dataReceived(json.dumps(config).encode())
            protocol.connectionLost(Failure(ResponseDone()))
        resp.deliverBody = Mock(side_effect=feed_response)
        agent.request = Mock(return_value=defer.succeed(resp))

        data = yield self.router.get_onionoo_details(agent)

        self.assertTrue('fingerprint' in data)
        self.assertTrue(data['fingerprint'] == "00786E43CCC5409753F25E36031C5CEA6EA43702")

    @defer.inlineCallbacks
    def test_onionoo_too_many_answers(self):
        agent = Mock()
        resp = Mock()
        resp.code = 200

        def feed_response(protocol):
            config = {
                "relays": [
                    {
                        "fingerprint": "00786E43CCC5409753F25E36031C5CEA6EA43702",
                    },
                    {
                        "fingerprint": "boom",
                    }
                ]
            }
            protocol.dataReceived(json.dumps(config).encode())
            protocol.connectionLost(Failure(ResponseDone()))
        resp.deliverBody = Mock(side_effect=feed_response)
        agent.request = Mock(return_value=defer.succeed(resp))

        with self.assertRaises(Exception) as ctx:
            yield self.router.get_onionoo_details(agent)

        self.assertTrue(
            "multiple relays for" in str(ctx.exception)
        )

    @defer.inlineCallbacks
    def test_onionoo_wrong_fingerprint(self):
        agent = Mock()
        resp = Mock()
        resp.code = 200

        def feed_response(protocol):
            config = {
                "relays": [
                    {
                        "fingerprint": "boom",
                    },
                ]
            }
            protocol.dataReceived(json.dumps(config).encode())
            protocol.connectionLost(Failure(ResponseDone()))
        resp.deliverBody = Mock(side_effect=feed_response)
        agent.request = Mock(return_value=defer.succeed(resp))

        with self.assertRaises(Exception) as ctx:
            yield self.router.get_onionoo_details(agent)

        self.assertTrue(
            " but got data for " in str(ctx.exception)
        )
