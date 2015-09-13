# -*- coding: utf-8 -*-
import unittest
import random
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.tests.handlers.test_user import TestUserInstance
from globaleaks.handlers import receiver, admin
from globaleaks.rest import errors


class TestReceiverInstance(TestUserInstance):
    _handler = receiver.ReceiverInstance

    # This test has for inharitance all the tests of TestReceiverInstance

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

    @inlineCallbacks
    def test_serialisation_receivertiplist(self):
        handler = self.request(user_id = self.dummyReceiver_1['id'], role='receiver')

        yield handler.get()

        expected_keys = ['creation_date', 'context_name', 'id', 'file_counter', 'questionnaire_hash', 'preview_schema', 'expiration_date', 'message_counter', 'access_counter', 'label', 'tor2web', 'comment_counter', 'last_access', 'preview']
        for receivertiplist_key in self.responses[0][0].keys():
            self.assertTrue(receivertiplist_key in expected_keys, "Missing %s key")
            expected_keys.remove(receivertiplist_key)

        self.assertTrue(len(expected_keys) == 0, "A key(s) has been removed from handler: %s" % expected_keys)


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

