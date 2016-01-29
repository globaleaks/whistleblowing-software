# -*- encoding: utf-8 -*-

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import event
from globaleaks.anomaly import Alarm
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.tests.test_anomaly import pollute_events_for_testing
from globaleaks.utils.token import Token, TokenList

class TestToken(helpers.TestGL):
    """
    This is an object testing class,
    to check the handler testing, see in
    test_anomalies
    """
    pollute_events_for_testing()

    stress_indicator = [ 'graph_captcha', 'human_captcha', 'proof_of_work' ]

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        # This is at the beginning
        event.EventTrackQueue.reset()

        pollute_events_for_testing()
        yield Alarm.compute_activity_level()

        # Token submission
        st = Token('submission')
        st.generate_token_challenge()

    def test_token(self):
        st = Token('submission')

        st_dict = st.serialize()

        self.assertEqual(st_dict['remaining_uses'], Token.MAX_USES)

        if st.graph_captcha:
            self.assertTrue(st.graph_captcha.has_key('answer'))
            self.assertTrue(isinstance(st.graph_captcha['answer'], list))

        if st.human_captcha:
            self.assertTrue(st.human_captcha.has_key('answer'))
            self.assertTrue(isinstance(st.human_captcha['answer'], unicode))

    @inlineCallbacks
    def test_token_create_and_get_upload_expire(self):
        file_list = []

        token_collection = []
        for i in xrange(20):
            st = Token('submission')

            token_collection.append(st)

        for t in token_collection:
            token = TokenList.get(t.id)

            yield self.emulate_file_upload(token, 3)

            for f in token.uploaded_files:
                self.assertTrue(os.path.exists(f['encrypted_path']))
                file_list.append(f['encrypted_path'])

        TokenList.reactor.pump([1] * TokenList.get_timeout())

        for t in token_collection:
            self.assertRaises(errors.TokenFailure, TokenList.get, t.id)

            for f in file_list:
                self.assertFalse(os.path.exists(f))



    def test_token_update_right_answer(self):
        token = Token('submission')

        token.human_captcha = {'question': '1 + 0','answer': 1}
        token.proof_of_work = False

        # validate with right value: OK
        token.update({'human_captcha_answer': 1})

        # verify that the challenge is marked as solved
        self.assertFalse(token.human_captcha)

    def test_token_update_wrong_answer(self):
        token = Token('submission')

        token.human_captcha = {'question': 'XXX','answer': 1}

        token.update({'human_captcha_answer': 0})

        # verify that the challenge is changed
        self.assertNotEqual(token.human_captcha['question'], 'XXX')

    def test_token_uses_limit(self):
        token = Token('submission')

        token.human_captcha = False
        token.proof_of_work = False

        # validate with right value: OK
        token.update({'human_captcha_answer': 1})

        for i in range(0, token.MAX_USES):
            token.use()

        # validate with right value but with no additional
        # attempts available: FAIL
        self.assertRaises(
            errors.TokenFailure,
            token.use
        )


    def test_proof_of_work_right_answer(self):
        # This is at the beginning
        event.EventTrackQueue.reset()

        token = Token('submission')

        difficulty = {
            'human_captcha': False,
            'graph_captcha': False,
            'proof_of_work': False
        }

        token.generate_token_challenge(difficulty)

        token = TokenList.get(token.id)
        # Note, this solution works with two '00' at the end, if the
        # difficulty changes, also this dummy value has to.
        token.proof_of_work = { 'question': "7GJ4Sl37AEnP10Zk9p7q" }

        # validate with right value: OK
        self.assertFalse(token.update({'proof_of_work_answer': 26}))

        # verify that the challenge is marked as solved
        self.assertFalse(token.proof_of_work)

    def test_proof_of_work_right_answer(self):
        token = Token('submission')

        difficulty = {
            'human_captcha': False,
            'graph_captcha': False,
            'proof_of_work': False
        }

        token.generate_token_challenge(difficulty)

        token = TokenList.get(token.id)
        # Note, this solution works with two '00' at the end, if the
        # difficulty changes, also this dummy value has to.
        token.proof_of_work = { 'question': "7GJ4Sl37AEnP10Zk9p7q" }

        # validate with right value: OK
        self.assertTrue(token.update({'proof_of_work_answer': 0}))
