# -*- coding: utf-8 -*-

import os

from globaleaks.anomaly import Alarm
from globaleaks.jobs import anomalies
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.token import Token, TokenList
from twisted.internet.defer import inlineCallbacks


class TestToken(helpers.TestGL):
    """
    This is an object testing class,
    to check the handler testing, see in
    test_anomalies
    """
    stress_indicator = ['human_captcha', 'proof_of_work']

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)
        TokenList.clear()

        self.pollute_events()

        yield anomalies.Anomalies().run()

    def test_token(self):
        st = Token(1, 'submission')

        st_dict = st.serialize()

        self.assertEqual(st_dict['remaining_uses'], Token.MAX_USES)

        if st.human_captcha:
            self.assertTrue(st.human_captcha.has_key('answer'))
            self.assertTrue(isinstance(st.human_captcha['answer'], int))

    @inlineCallbacks
    def test_token_create_and_get_upload_expire(self):
        file_list = []

        token_collection = []
        for _ in range(20):
            st = Token(1, 'submission')
            token_collection.append(st)

        for t in token_collection:
            token = TokenList.get(t.id)

            yield self.emulate_file_upload(token, 3)

            for f in token.uploaded_files:
                self.assertTrue(os.path.exists(f['path']))
                file_list.append(f['path'])

        self.test_reactor.advance(TokenList.get_timeout()+1)

        for t in token_collection:
            self.assertRaises(errors.TokenFailure, TokenList.get, t.id)

            for f in file_list:
                self.assertFalse(os.path.exists(f))

    def test_token_update_right_answer(self):
        token = Token(1, 'submission')
        token.solve()

        token.human_captcha = {'question': '1 + 0', 'answer': 1, 'solved': False}

        # validate with right value: OK
        self.assertTrue(token.update({'human_captcha_answer': 1}))

        # verify that the challenge is marked as solved
        self.assertTrue(token.human_captcha['solved'])

    def test_token_update_wrong_answer(self):
        token = Token(1, 'submission')
        token.solve()

        token.human_captcha = {'question': 'XXX', 'answer': 1, 'solved': False}

        token.update({'human_captcha_answer': 0})

        # verify that the challenge is changed
        self.assertNotEqual(token.human_captcha['question'], 'XXX')

    def test_token_usage_limit(self):
        token = Token(1, 'submission')
        token.solve()

        token.human_captcha = {'question': 'XXX', 'answer': 1, 'solved': False}

        # validate with right value: OK
        token.update({'human_captcha_answer': 1})

        for _ in range(token.MAX_USES-1):
            token.use()

        # validate with right value but with no additional
        # attempts available: FAIL
        self.assertRaises(errors.TokenFailure, token.use)

    def test_proof_of_work_wrong_answer(self):
        token = Token(1, 'submission')
        token.solve()

        # Note, this solution works with two '00' at the end, if the
        # difficulty changes, also this dummy value has to.
        token.proof_of_work = {'question': "7GJ4Sl37AEnP10Zk9p7q", 'solved': False}

        self.assertFalse(token.update({'proof_of_work_answer': 0}))
        # validate with right value: OK
        self.assertRaises(errors.TokenFailure, token.use)

    def test_proof_of_work_right_answer(self):
        token = Token(1, 'submission')
        token.solve()

        # Note, this solution works with two '00' at the end, if the
        # difficulty changes, also this dummy value has to.
        token.proof_of_work = {'question': "7GJ4Sl37AEnP10Zk9p7q", 'solved': False}

        # validate with right value: OK
        self.assertTrue(token.update({'proof_of_work_answer': 26}))
        token.use()

    def test_tokens_garbage_collected(self):
        self.assertTrue(len(TokenList) == 0)

        for _ in range(100):
            Token(1, 'submission')

        self.assertTrue(len(TokenList) == 100)

        self.test_reactor.advance(TokenList.get_timeout()+1)

        self.assertTrue(len(TokenList) == 0)
