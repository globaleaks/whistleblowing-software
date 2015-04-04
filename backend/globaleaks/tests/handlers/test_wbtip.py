# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.handlers import wbtip


class TestWBTipInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = wbtip.WBTipInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user.user_id = wbtip_desc['wbtip_id']

            yield handler.get()

class TestWBTipCommentCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = wbtip.WBTipCommentCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user.user_id = wbtip_desc['wbtip_id']

            yield handler.get()

    @inlineCallbacks
    def test_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb', body=json.dumps(body))
            handler.current_user.user_id = wbtip_desc['wbtip_id']

            yield handler.post()

class TestWBTipMessageCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = wbtip.WBTipMessageCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user.user_id = wbtip_desc['wbtip_id']

            for rcvr_id in wbtip_desc['wbtip_receivers']:
                yield handler.get(rcvr_id)

    @inlineCallbacks
    def test_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb', body=json.dumps(body))
            handler.current_user.user_id = wbtip_desc['wbtip_id']

            for rcvr_id in wbtip_desc['wbtip_receivers']:
                yield handler.post(rcvr_id)

class TestWBTipReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = wbtip.WBTipReceiversCollection

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user.user_id = wbtip_desc['wbtip_id']

            yield handler.get()
