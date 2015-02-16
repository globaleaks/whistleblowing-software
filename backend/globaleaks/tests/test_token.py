# -*- encoding: utf-8 -*-


from twisted.trial import unittest
from twisted.internet import task
from globaleaks import anomaly
from globaleaks.utils.token import Token, TokenList
from twisted.trial.util import DirtyReactorAggregateError


from twisted.internet import task
import globaleaks.utils.token.reactor
globaleaks.utils.token.reactor = task.Clock()

class TestToken(unittest.TestCase):
    """
    This is an object testing class,
    to check the handler testing, see in
    test_anomalies
    """

    shared_alarm_obj = anomaly.Alarm()
    stress_indicator = [ 'graph_captcha', 'human_captcha', 'proof_of_work' ]

    def test_token_obj_zero_stress(self):

        # This is at the beginning
        anomaly.EventTrackQueue.reset()

        # Token submission
        st = Token('submission', context_id="ignored", debug=True)
        st.set_difficulty(TestToken.shared_alarm_obj.get_token_difficulty())

        for indicator in TestToken.stress_indicator:
            self.assertFalse( getattr(st, indicator), indicator )

        st_dict = st.serialize_token()
        self.assertEqual(st_dict['usages'], 1)

        try:
            st.expire()
        except DirtyReactorAggregateError:
            pass



    def test_token_obj_level1_stress(self):

        mock_high_difficulty = {
            'human_captcha': True,
            'graph_captcha': True,
            'proof_of_work': True,
        }

        # Token submission
        st = Token('submission', context_id='ignored', debug=True)
        st.set_difficulty(mock_high_difficulty)

        self.assertTrue( st.graph_captcha.has_key('answer') )
        self.assertTrue( st.human_captcha.has_key('answer') )

        # TODO make a proper evaluation of captcha creation
        st_dict = st.serialize_token()

        # self.assertTrue( isinstance(st.graph_captcha['question'], unicode) )
        self.assertTrue( isinstance(st.graph_captcha['answer'], list ) )

        self.assertTrue( isinstance(st.human_captcha['question'], unicode) )
        self.assertTrue( isinstance(st.human_captcha['answer'], unicode) )

        st_dict = st.serialize_token()
        self.assertEqual(st_dict['usages'], 1)

        try:
            st.expire()
        except DirtyReactorAggregateError:
            pass


    def test_token_create_and_get(self):

        # This is at the beginning
        anomaly.EventTrackQueue.reset()

        token_collection = []
        for i in xrange(20):

            st = Token('submission', context_id='ignored')
            st.set_difficulty(TestToken.shared_alarm_obj.get_token_difficulty())

            token_collection.append( st )

        # Here we're testing the 'Too early usage'
        from globaleaks.rest.errors import TokenRequestError

        for t in token_collection:
            retrieve_token = TokenList.validate_token_id(t.id)

            self.assertRaises(
                TokenRequestError,
                retrieve_token['token_object'].validate, retrieve_token
            )

            # and check exactly the reason:
            try:
                retrieve_token['token_object'].validate(retrieve_token)
            except TokenRequestError as TRE:
                self.assertEqual(TRE.reason,
                                 "Token Error: Too early to use this token ")

            try:
                retrieve_token['token_object'].expire()
            except DirtyReactorAggregateError:
                pass



