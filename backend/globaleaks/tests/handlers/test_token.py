# -*- encoding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, returnValue

# override GLSettings
from globaleaks import event
from globaleaks.anomaly import Alarm
from globaleaks.orm import transact_ro
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import wbtip, token
from globaleaks.handlers.admin.context import get_context_steps
from globaleaks.handlers.admin.receiver import create_receiver
from globaleaks.rest import errors
from globaleaks.models import InternalTip
from globaleaks.utils.token import Token
from globaleaks.tests.test_anomaly import pollute_events_for_testing

class Test_TokenCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = token.TokenCreate

    def assert_default_token_values(self, token):
        self.assertEqual(token['type'], u'submission')
        self.assertEqual(token['start_validity_secs'], 0)
        self.assertEqual(token['end_validity_secs'], 10800)
        self.assertEqual(token['remaining_uses'], Token.MAX_USES)
        self.assertEqual(token['human_captcha_answer'], 0)
        self.assertEqual(token['graph_captcha_answer'], '')

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
        pollute_events_for_testing()
        yield Alarm.compute_activity_level()

        token = Token('submission')

        token.human_captcha = {'question': 'XXX','answer': 1}
        token.proof_of_work = False

        request_payload = token.serialize()

        request_payload['human_captcha_answer'] = 1

        handler = self.request(request_payload)
        yield handler.put(token.id)

        self.assertEqual(self.responses[0]['human_captcha'], False)

    @inlineCallbacks
    def test_put_wrong_answer(self):
        pollute_events_for_testing()
        yield Alarm.compute_activity_level()

        token = Token('submission')

        token.human_captcha = {'question': 'XXX','answer': 1}
        token.proof_of_work = False

        request_payload = token.serialize()

        request_payload['human_captcha_answer'] = 2

        handler = self.request(request_payload)
        yield handler.put(token.id)

        self.assertNotEqual(self.responses[0]['human_captcha'], False)

        # verify that the question is changed
        self.assertNotEqual(self.responses[0]['human_captcha'], 'XXX')

