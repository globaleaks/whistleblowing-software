# -*- coding: utf-8 -*-
import unittest
import random
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import receiver, admin
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.tests.handlers.test_user import TestUserInstance


class TestReceiverInstance(TestUserInstance):
    _handler = receiver.ReceiverInstance

    # This test has for inharitance all the tests of TestUserInstance

    @inlineCallbacks
    def test_ping_mail_change(self):
        handler = self.request(user_id = self.rcvr_id, role='receiver')

        yield handler.get()

        self.responses[0]['ping_mail_address'] = 'ortomio@x.com'

        handler = self.request(self.responses[0], user_id = self.rcvr_id, role='receiver')
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
        for _ in xrange(3):
            yield self.perform_full_submission_actions()

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')
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

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')

        for rtip in rtips:
            self.assertNotEqual(postpone_map[rtip['id']], rtip['expiration_date'])

    @inlineCallbacks
    def test_put_delete(self):
        for _ in xrange(3):
            yield self.perform_full_submission_actions()

        handler = self.request(user_id = self.dummyReceiver_1['id'], role='receiver')

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')
        rtips_ids = [rtip['id'] for rtip in rtips]

        data_request = {
            'operation': 'delete',
            'rtips': rtips_ids
        }

        handler = self.request(data_request, user_id = self.dummyReceiver_1['id'], role='receiver')
        yield handler.put()

        rtips = yield receiver.get_receivertip_list(self.dummyReceiver_1['id'], 'en')

        self.assertEqual(len(rtips), 0)
