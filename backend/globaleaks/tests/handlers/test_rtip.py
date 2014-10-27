# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import admin, rtip
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.models import ReceiverTip

class TestRTipInstance(helpers.TestHandler):
    _handler = rtip.RTipInstance

    @inlineCallbacks
    def test_001_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_002_delete_global_delete_true(self):
        body = {
            'global_delete' : True,
            'is_pertinent': False,
            'extend': False
        }

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), 2)

        # we deleete the first and then we verify that the second does not exist anymore
        handler = self.request(role='receiver', body=json.dumps(body))
        handler.current_user.user_id = rtips_desc[0]['receiver_id']
        yield handler.delete(rtips_desc[0]['rtip_id'])

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), 0)

    @inlineCallbacks
    def test_003_delete_global_delete_false(self):
        body = {
            'global_delete' : False,
            'is_pertinent': False,
            'extend': False
        }

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), 2)

        # we delete the first than we verify that the second still exists
        handler = self.request(role='receiver', body=json.dumps(body))
        handler.current_user.user_id = rtips_desc[0]['receiver_id']
        yield handler.delete(rtips_desc[0]['rtip_id'])

        rtips_desc = yield self.get_rtips()

        self.assertEqual(len(rtips_desc), 1)

    @inlineCallbacks
    def test_004_delete_unexistent_tip_by_existent_and_logged_receiver(self):
        body = {
            'global_delete' : True,
            'is_pertinent': False,
            'extend': False
        }

        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)

    @inlineCallbacks
    def test_004_delete_existent_tip_by_existent_and_logged_but_wrong_receiver(self):
        body = {
            'global_delete' : True,
            'is_pertinent': False,
            'extend': False
        }

        rtips_desc = yield self.get_rtips()

        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            self.assertFailure(handler.delete("unexistent_tip"), errors.TipIdNotFound)

class TestRTipCommentCollection(helpers.TestHandler):
    _handler = rtip.RTipCommentCollection

    @inlineCallbacks
    def test_001_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_002_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.post(rtip_desc['rtip_id'])

class TestReceiverMsgCollection(helpers.TestHandler):
    _handler = rtip.ReceiverMsgCollection

    @inlineCallbacks
    def test_001_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])

    @inlineCallbacks
    def test_002_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver', body=json.dumps(body))
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.post(rtip_desc['rtip_id'])

class TestRTipReceiversCollection(helpers.TestHandler):
    _handler = rtip.RTipReceiversCollection

    @inlineCallbacks
    def test_001_get(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rtip_desc['receiver_id']

            yield handler.get(rtip_desc['rtip_id'])

