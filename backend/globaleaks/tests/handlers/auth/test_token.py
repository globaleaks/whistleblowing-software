# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.auth import token
from globaleaks.jobs import anomalies
from globaleaks.tests import helpers


class Test_Token(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenHandler

    def assert_default_token_values(self, token):
        self.assertEqual(token['complexity'], 4)

    @inlineCallbacks
    def test_post(self):
        yield anomalies.Anomalies().run()

        handler = self.request({})

        handler.request.client_using_tor = True

        response = yield handler.post()

        self.assert_default_token_values(response)
