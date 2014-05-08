# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests
from globaleaks.tests import helpers
from globaleaks.handlers import receiver, admin
from globaleaks.settings import GLSetting

class TestReceiverInstance(helpers.TestHandler):
    _handler = receiver.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list()
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user['user_id'] = rcvr['id']

            yield handler.get()

    @inlineCallbacks
    def test_put(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list()
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user['user_id'] = rcvr['id']

            yield handler.get()

            # this need to be populated manually
            self.responses[0]['password'] = ''
            self.responses[0]['old_password'] = ''

            handler = self.request(self.responses[0], role='receiver')
            handler.current_user['user_id'] = rcvr['id']
            yield handler.put()

class TestTipsCollection(helpers.TestHandler):
    _handler = receiver.TipsCollection

    @inlineCallbacks
    def test_get(self):
        # FIXME currently the helpers.TestHandler do not populate any tip
        #       so that very few code is covered. 
        handler = self.request(role='receiver')
        yield handler.get()
