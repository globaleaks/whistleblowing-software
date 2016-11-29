# -*- encoding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.anomaly import Alarm
from globaleaks.handlers import token
from globaleaks.tests import helpers
from globaleaks.utils.token import Token
from globaleaks.rest import errors
from globaleaks.settings import GLSettings

class Test_TokenCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenCreate

    def assert_default_token_values(self, token):
        self.assertEqual(token['type'], u'submission')
        self.assertEqual(token['remaining_uses'], Token.MAX_USES)
        self.assertEqual(token['human_captcha_answer'], 0)

    @inlineCallbacks
    def test_post(self):
        yield Alarm.compute_activity_level()

        handler = self.request({'type': 'submission'})

        yield handler.post()

        token = self.responses[0]

        self.assert_default_token_values(token)


class Test_TokenInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenInstance

    @inlineCallbacks
    def test_put_right_answer(self):
        self.pollute_events()
        yield Alarm.compute_activity_level()

        token = Token('submission')
        token.human_captcha = {'question': 'XXX','answer': 1, 'solved': False}
        token.proof_of_work['solved'] = True

        request_payload = token.serialize()
        request_payload['human_captcha_answer'] = 1

        handler = self.request(request_payload)

        yield handler.put(token.id)

        token.use()

        self.assertFalse(self.responses[0]['human_captcha'])
        self.assertTrue(token.human_captcha['solved'])

    @inlineCallbacks
    def test_put_wrong_answer(self):
        self.pollute_events()
        yield Alarm.compute_activity_level()

        token = Token('submission')

        token.human_captcha = {'question': 'XXX','answer': 1, 'solved': False}

        request_payload = token.serialize()

        request_payload['human_captcha_answer'] = 883

        handler = self.request(request_payload)
        self.assertRaises(errors.TokenFailure, handler.put, token.id)
