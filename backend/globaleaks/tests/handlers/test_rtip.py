# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import admin, rtip
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.models import ReceiverTip

class TestRTipInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.RTipInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_submission()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_put(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            self.responses = []

            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']
            yield handler.get(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 200)

            self.responses[0]['extend'] = True

            handler = self.request(self.responses[0], role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']
            yield handler.put(rtip_desc['rtip_id'])
            self.assertEqual(handler.get_status(), 202)

    @inlineCallbacks
    def test_delete_global_delete_true(self):
        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 2)

        body = {
            'global_delete' : True,
            'extend': False
        }

        # we deleete the first and then we verify that the second does not exist anymore
        handler = self.request(role='receiver', body=json.dumps(body))
        handler.current_user.user_id = rtips_desc[0]['receiver_id']
        yield handler.delete(rtips_desc[0]['rtip_id'])

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), 0)

    @inlineCallbacks
    def test_delete_global_delete_false(self):
        rtips_desc = yield self.get_rtips()
        self.assertEqual(len(rtips_desc), 2)

        body = {
            'global_delete' : False,
            'extend': False
        }

        # we delete the first than we verify that the second still exists
        handler = self.request(role='receiver', body=json.dumps(body))
        handler.current_user.user_id = rtips_desc[0]['receiver_id']
        yield handler.delete(rtips_desc[0]['rtip_id'])

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), 1)

    @inlineCallbacks
    def test_delete_unexistent_tip_by_existent_and_logged_receiver(self):
        body = {
            'global_delete' : True,
            'extend': False
        }

        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)

    @inlineCallbacks
    def test_delete_existent_tip_by_existent_and_logged_but_wrong_receiver(self):
        body = {
            'global_delete' : True,
            'extend': False
        }

        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)

    @inlineCallbacks
    def test_get_banned_for_too_much_accesses(self):
        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            for x in range(0, 10):
               handler = self.request(role='receiver')
               handler.current_user.user_id = rtip_desc['receiver_id']
               handler.get(rtip_desc['rtip_id'])

            self.assertFailure(handler.get(rtip_desc['rtip_id']), errors.AccessLimitExceeded)

class TestRTipCommentCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.RTipCommentCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_submission()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.post(rtip_desc['rtip_id'])

class TestReceiverMsgCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.ReceiverMsgCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_submission()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.post(rtip_desc['rtip_id'])

class TestRTipReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = rtip.RTipReceiversCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_submission()

    @inlineCallbacks
    def test_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])
