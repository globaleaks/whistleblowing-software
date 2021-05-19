# -*- coding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs import anomalies
from globaleaks.tests import helpers


class TestToken(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        self.state.tokens.clear()

        self.pollute_events()

        yield anomalies.Anomalies().run()

    def test_proof_of_work_wrong_answer(self):
        token = self.getToken()

        self.assertFalse(token.update(0))
        # validate with right value: OK
        self.assertRaises(Exception, self.state.tokens.validate, token.id)

    def test_proof_of_work_right_answer(self):
        token = self.getToken()

        # validate with right value: OK
        self.assertTrue(token.update(token.answer))
        self.state.tokens.validate(token.id)

    def test_tokens_garbage_collected(self):
        self.assertTrue(len(self.state.tokens) == 0)

        for _ in range(100):
            self.state.tokens.new(1)

        self.assertTrue(len(self.state.tokens) == 100)

        self.test_reactor.advance(self.state.tokens.timeout + 1)

        self.assertTrue(len(self.state.tokens) == 0)
