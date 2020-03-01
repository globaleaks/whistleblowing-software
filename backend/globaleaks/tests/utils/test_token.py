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

    def test_token_create_and_get_upload_expire(self):
        file_list = []

        token_collection = []
        for _ in range(20):
            st = self.state.tokens.new(1)
            token_collection.append(st)

        for t in token_collection:
            token = self.state.tokens.get(t.id)

            self.emulate_file_upload(token, 3)

            for f in token.uploaded_files:
                filepath = os.path.abspath(os.path.join(self.state.settings.tmp_path, f['filename']))
                self.assertTrue(os.path.exists(filepath))
                file_list.append(filepath)

        self.test_reactor.advance(self.state.tokens.get_timeout() + 1)

        for t in token_collection:
            self.assertRaises(Exception, self.state.tokens.get, t.id)

            for filepath in file_list:
                self.assertFalse(os.path.exists(filepath))

    def test_proof_of_work_wrong_answer(self):
        token = self.getToken()

        self.assertFalse(token.update(0))
        # validate with right value: OK
        self.assertRaises(Exception, self.state.tokens.use, token.id)

    def test_proof_of_work_right_answer(self):
        token = self.getToken()

        # validate with right value: OK
        self.assertTrue(token.update(token.answer))
        self.state.tokens.use(token.id)

        # verify that token reuse is blocked
        self.assertRaises(Exception, self.state.tokens.get, token.id)

    def test_tokens_garbage_collected(self):
        self.assertTrue(len(self.state.tokens) == 0)

        for _ in range(100):
            self.state.tokens.new(1)

        self.assertTrue(len(self.state.tokens) == 100)

        self.test_reactor.advance(self.state.tokens.get_timeout()+1)

        self.assertTrue(len(self.state.tokens) == 0)
