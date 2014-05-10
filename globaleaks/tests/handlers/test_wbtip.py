# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import admin, wbtip
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.models import ReceiverTip

class TestWBTipInstance(helpers.TestHandler):
    _handler = wbtip.WBTipInstance

    @inlineCallbacks
    def test_001_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user['user_id'] = wbtip_desc['wbtip_id']

            yield handler.get()

class TestWBTipCommentCollection(helpers.TestHandler):
    _handler = wbtip.WBTipCommentCollection

    @inlineCallbacks
    def test_001_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user['user_id'] = wbtip_desc['wbtip_id']

            yield handler.get()

    @inlineCallbacks
    def test_002_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb', body=json.dumps(body))
            handler.current_user['user_id'] = wbtip_desc['wbtip_id']

            yield handler.post(wbtip_desc['wbtip_id'])

class TestWBTipMessageCollection(helpers.TestHandler):
    _handler = wbtip.WBTipMessageCollection

    @inlineCallbacks
    def test_001_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user['user_id'] = wbtip_desc['wbtip_id']

            for rcvr_id in wbtip_desc['wbtip_receivers']:
                yield handler.get(rcvr_id)

    @inlineCallbacks
    def test_002_post(self):
        body = {
            'content' : "can you provide an evidence of what you are telling?",
        }

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb', body=json.dumps(body))
            handler.current_user['user_id'] = wbtip_desc['wbtip_id']

            for rcvr_id in wbtip_desc['wbtip_receivers']:
                yield handler.post(rcvr_id)

class TestWBTipReceiversCollection(helpers.TestHandler):
    _handler = wbtip.WBTipReceiversCollection

    @inlineCallbacks
    def test_001_get(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb')
            handler.current_user['user_id'] = wbtip_desc['wbtip_id']

            yield handler.get()
