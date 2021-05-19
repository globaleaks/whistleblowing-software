# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import token
from globaleaks.jobs import anomalies
from globaleaks.tests import helpers


class Test_TokenCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenCreate

    def assert_default_token_values(self, token):
        self.assertEqual(token['ttl'], 60)

    @inlineCallbacks
    def test_post(self):
        yield anomalies.Anomalies().run()

        handler = self.request({})

        handler.request.client_using_tor = True

        response = yield handler.post()

        self.assert_default_token_values(response)


class Test_TokenInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenInstance

    @inlineCallbacks
    def test_put_right_answer(self):
        self.pollute_events()
        yield anomalies.Anomalies().run()

        token = self.getToken()

        request_payload = token.serialize()
        request_payload['answer'] = token.answer

        handler = self.request(request_payload)

        yield handler.put(token.id)

        token.tokenlist.validate(token.id)

        self.assertTrue(token.solved)

    @inlineCallbacks
    def test_put_wrong_answer(self):
        self.pollute_events()
        yield anomalies.Anomalies().run()

        token = self.getToken()

        request_payload = token.serialize()
        request_payload['answer'] = 0

        handler = self.request(request_payload)

        yield handler.put(token.id)

        self.assertRaises(Exception, token.tokenlist.validate, token.id)
