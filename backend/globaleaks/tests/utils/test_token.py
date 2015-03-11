# -*- encoding: utf-8 -*-


from twisted.trial import unittest
from twisted.internet import task
from globaleaks import anomaly
from globaleaks.utils.token import Token, TokenList
from twisted.trial.util import DirtyReactorAggregateError

from twisted.internet import task

class TestToken(unittest.TestCase):
    """
    This is an object testing class,
    to check the handler testing, see in
    test_anomalies
    """

    shared_alarm_obj = anomaly.Alarm()
    stress_indicator = [ 'graph_captcha', 'human_captcha', 'proof_of_work' ]

    def test_token_obj_zero_stress(self):

        c = task.Clock() # deterministic clock

        # This is at the beginning
        anomaly.EventTrackQueue.reset()

        # Token submission
        st = Token('submission', context_id="ignored", reactor=c)
        st.set_difficulty(TestToken.shared_alarm_obj.get_token_difficulty())

        for indicator in TestToken.stress_indicator:
            self.assertFalse(getattr(st, indicator), indicator)

        st_dict = st.serialize_token()
        self.assertEqual(st_dict['remaining_allowed_attempts'], Token.MAXIMUM_ATTEMPTS_PER_TOKEN)


    def test_token_obj_level1_stress(self):

        c = task.Clock() # deterministic clock

        mock_high_difficulty = {
            'human_captcha': True,
            'graph_captcha': True,
            'proof_of_work': True,
        }

        # Token submission
        st = Token('submission', context_id='ignored', reactor=c)
        st.set_difficulty(mock_high_difficulty)

        st_dict = st.serialize_token()

        if st.graph_captcha:
            self.assertTrue(st.graph_captcha.has_key('answer'))
            self.assertTrue(isinstance(st.graph_captcha['answer'], list ))

        if st.human_captcha:
            self.assertTrue(st.human_captcha.has_key('answer'))
            self.assertTrue(isinstance(st.human_captcha['answer'], unicode))

        self.assertEqual(st_dict['remaining_allowed_attempts'], Token.MAXIMUM_ATTEMPTS_PER_TOKEN)

    def test_token_create_and_get(self):

        c = task.Clock() # deterministic clock

        # This is at the beginning
        anomaly.EventTrackQueue.reset()

        token_collection = []
        for i in xrange(20):

            st = Token('submission', context_id='ignored', reactor=c)
            st.set_difficulty(TestToken.shared_alarm_obj.get_token_difficulty())

            token_collection.append(st)

        # Here we're testing the 'Too early usage'
        from globaleaks.rest.errors import TokenFailure

        for t in token_collection:
            token = TokenList.get(t.id)

            difficulty = {
                'human_captcha': True,
                'graph_captcha': False,
                'proof_of_work': False,
            }

            token.set_difficulty(difficulty)

            self.assertRaises(
                TokenFailure,
                token.validate, {'human_captcha_answer': 0}
            )


