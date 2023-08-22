# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers import recipient
from globaleaks.orm import transact
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_never


@transact
def set_expiration_of_all_rtips_to_unlimited(session):
    session.query(models.InternalTip).update({'expiration_date': datetime_never()})


class TestTipsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = recipient.TipsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')
        rtips = yield handler.get()
        for idx in range(len(rtips)):
            self.assertEqual(rtips[idx]['file_count'], 2)
            self.assertEqual(rtips[idx]['comment_count'], 3)


class TestOperations(helpers.TestHandlerWithPopulatedDB):
    _handler = recipient.Operations

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_put_revoke_and_grant(self):
        rtips = yield recipient.get_receivertips(1, self.dummyReceiver_1['id'], helpers.USER_PRV_KEY, 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        yield self.test_model_count(models.ReceiverTip, 4)

        data_request = {
            'operation': 'revoke',
            'args': {
              'receiver': self.dummyReceiver_2['id'],
              'rtips': rtips_ids
            }
        }

        handler = self.request(data_request, user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        yield self.test_model_count(models.ReceiverTip, 2)

        data_request = {
            'operation': 'grant',
            'args': {
              'receiver': self.dummyReceiver_2['id'],
              'rtips': rtips_ids
            }
        }

        handler = self.request(data_request, user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        yield self.test_model_count(models.ReceiverTip, 4)
