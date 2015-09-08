# -*- encoding: utf-8 -*-

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import anomaly, event
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

    shared_alarm_obj = anomaly.Alarm()
    stress_indicator = [ 'graph_captcha', 'human_captcha', 'proof_of_work' ]

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        # This is at the beginning
        event.EventTrackQueue.reset()

        pollute_events_for_testing()
        yield anomaly.compute_activity_level()

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

            token.expire()

            self.assertRaises(
                errors.TokenFailure,
                TokenList.get, t.id
            )

            for f in file_list:
                self.assertFalse(os.path.exists(f))

    def test_token_update_right_answer(self):
        token = Token('submission')

        token.human_captcha = {'question': '1 + 0','answer': 1}

        # validate with right value: OK
        token.update({'human_captcha_answer': 1})

        # verify that the challenge is changed
        self.assertFalse(token.human_captcha)

    def test_token_update_wrong_answer(self):
        token = Token('submission')

        token.human_captcha = {'question': 'XXX','answer': 1}

        token.update({'human_captcha_answer': 0})

        # verify that the challenge is changed
        self.assertNotEqual(token.human_captcha['question'], 'XXX')

    def test_token_uses_limit(self):
        token = Token('submission')

        token.human_captcha = {'question': '1 + 0','answer': 1}

        # validate with right value: OK
        token.update({'human_captcha_answer': 1})

        for i in range(0, token.MAX_USES):
            token.use()

        # validate with right value but with no additional
        # attemps available: FAIL
        self.assertRaises(
            errors.TokenFailure,
            token.use
        )
