# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.handlers.admin import receiver as admin_receiver
from globaleaks.handlers import receiver
from globaleaks.orm import transact
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_never
from twisted.internet.defer import inlineCallbacks


@transact
def set_expiration_of_all_rtips_to_unlimited(session):
    session.query(models.InternalTip).update({'expiration_date': datetime_never()})


class TestUserInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        self.rcvr_id = (yield admin_receiver.get_receiver_list(1, 'en'))[0]['id']

    @inlineCallbacks
    def test_disable_tip_notification(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        response = yield handler.get()

        response['tip_notification'] = False

        handler = self.request(response, user_id = self.rcvr_id, role='receiver')
        yield handler.put()


class TestTipsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        handler = self.request(user_id=self.dummyReceiver_1['id'], role='receiver')
        yield handler.get()


class TestTipsOperations(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsOperations

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_put_postpone(self):
        for _ in range(3):
            yield self.perform_full_submission_actions()

        yield set_expiration_of_all_rtips_to_unlimited()

        rtips = yield receiver.get_receivertip_list(1, self.dummyReceiver_1['id'], 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        postpone_map = {}
        for rtip in rtips:
            postpone_map[rtip['id']] = rtip['expiration_date']

        data_request = {
            'operation': 'postpone',
            'rtips': rtips_ids
        }

        handler = self.request(data_request, user_id = self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        rtips = yield receiver.get_receivertip_list(1, self.dummyReceiver_1['id'], 'en')

        for rtip in rtips:
            self.assertNotEqual(postpone_map[rtip['id']], rtip['expiration_date'])

    @inlineCallbacks
    def test_put_delete(self):
        for _ in range(3):
            yield self.perform_full_submission_actions()

        rtips = yield receiver.get_receivertip_list(1, self.dummyReceiver_1['id'], 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        data_request = {
            'operation': 'delete',
            'rtips': rtips_ids
        }

        handler = self.request(data_request, user_id = self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        #rtips = yield receiver.get_receivertip_list(1, self.dummyReceiver_1['id'], 'en')

        #self.assertEqual(len(rtips), 0)
