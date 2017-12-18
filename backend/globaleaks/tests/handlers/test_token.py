# -*- coding: utf-8 -*-
from globaleaks.jobs import anomalies
from globaleaks.handlers import token
from globaleaks.tests import helpers
from globaleaks.utils.token import Token
from twisted.internet.defer import inlineCallbacks


class Test_TokenCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenCreate

    def assert_default_token_values(self, token):
        self.assertEqual(token['type'], u'submission')
        self.assertEqual(token['remaining_uses'], Token.MAX_USES)
        self.assertEqual(token['human_captcha_answer'], 0)

    @inlineCallbacks
    def test_post(self):
        yield anomalies.Anomalies().run()

        handler = self.request({'type': 'submission'})

        handler.request.client_using_tor = True

        response = yield handler.post()

        self.assert_default_token_values(response)


class Test_TokenInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenInstance

    @inlineCallbacks
    def test_put_right_answer(self):
        self.pollute_events()
        yield anomalies.Anomalies().run()

        token = Token(1, 'submission')
        token.human_captcha = {'question': 'XXX','answer': 1, 'solved': False}
        token.proof_of_work['solved'] = True

        request_payload = token.serialize()
        request_payload['human_captcha_answer'] = 1

        handler = self.request(request_payload)

        response = yield handler.put(token.id)

        token.use()

        self.assertFalse(response['human_captcha'])
        self.assertTrue(token.human_captcha['solved'])

    @inlineCallbacks
    def test_put_wrong_answer(self):
        self.pollute_events()
        yield anomalies.Anomalies().run()

        token = Token(1, 'submission')

        orig_question = u'77+33'
        token.human_captcha = {'question': orig_question,'answer': 1, 'solved': False}

        request_payload = token.serialize()

        request_payload['human_captcha_answer'] = 883

        handler = self.request(request_payload)
        new_token = yield handler.put(token.id)

        self.assertFalse(token.human_captcha['solved'])

        self.assertEqual(new_token['human_captcha'], token.human_captcha['question'])
        self.assertNotEqual(new_token['human_captcha'], orig_question)

        self.assertIsNot(new_token['human_captcha'], False)
        self.assertNotIn('human_captcha_anwser', new_token)
