# -*- encoding: utf-8 -*-

import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import anomaly, event
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.token import Token, TokenList

class TestToken(helpers.TestGL):
    """
    This is an object testing class,
    to check the handler testing, see in
    test_anomalies
    """

    shared_alarm_obj = anomaly.Alarm()
    stress_indicator = [ 'graph_captcha', 'human_captcha', 'proof_of_work' ]

    def test_token_obj_zero_stress(self):

        # This is at the beginning
        event.EventTrackQueue.reset()

        # Token submission
        st = Token('submission', context_id="ignored")
        st.set_difficulty(TestToken.shared_alarm_obj.get_token_difficulty())

        for indicator in TestToken.stress_indicator:
            self.assertFalse(getattr(st, indicator), indicator)

        st_dict = st.serialize_token()
        self.assertEqual(st_dict['remaining_allowed_attempts'], Token.MAXIMUM_ATTEMPTS_PER_TOKEN)


    def test_token_obj_level1_stress(self):

        mock_high_difficulty = {
            'human_captcha': True,
            'graph_captcha': True,
            'proof_of_work': True,
        }

        # Token submission
        st = Token('submission', context_id='ignored')
        st.set_difficulty(mock_high_difficulty)

        st_dict = st.serialize_token()

        if st.graph_captcha:
            self.assertTrue(st.graph_captcha.has_key('answer'))
            self.assertTrue(isinstance(st.graph_captcha['answer'], list))

        if st.human_captcha:
            self.assertTrue(st.human_captcha.has_key('answer'))
            self.assertTrue(isinstance(st.human_captcha['answer'], unicode))

        self.assertEqual(st_dict['remaining_allowed_attempts'], Token.MAXIMUM_ATTEMPTS_PER_TOKEN)

    @inlineCallbacks
    def test_token_create_and_get_upload_expire(self):
        # This is at the beginning
        event.EventTrackQueue.reset()

        file_list = []

        token_collection = []
        for i in xrange(20):
            st = Token('submission', context_id='ignored')
            st.set_difficulty(TestToken.shared_alarm_obj.get_token_difficulty())

            token_collection.append(st)

        for t in token_collection:
            token = TokenList.get(t.id)

            difficulty = {
                'human_captcha': True,
                'graph_captcha': False,
                'proof_of_work': False,
            }

            token.set_difficulty(difficulty)

            self.assertRaises(
                errors.TokenFailure,
                token.validate, {'human_captcha_answer': 0}
            )


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

    def test_token_validate(self):
        # This is at the beginning
        event.EventTrackQueue.reset()

        token = Token('submission', context_id='ignored')

        difficulty = {
            'human_captcha': True,
            'graph_captcha': False,
            'proof_of_work': False,
        }

        token.set_difficulty(difficulty)

        token = TokenList.get(token.token_id)
        token.human_captcha = { 'answer': 1 }
        token.remaining_allowed_attempts = 1

        # validate with right value: OK
        token.validate({'human_captcha_answer': 1})

        # validate with wrong value: FAIL
        self.assertRaises(
            errors.TokenFailure,
            token.validate, {'human_captcha_answer': 0}
        )

        # validate with right value but with no additional
        # attemps available: FAIL
        self.assertRaises(
            errors.TokenFailure,
            token.validate, {'human_captcha_answer': 1}
        )
