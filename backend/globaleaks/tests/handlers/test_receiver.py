# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests
from globaleaks.tests import helpers
from globaleaks.handlers import receiver, admin
from globaleaks.settings import GLSetting

class TestReceiverInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list()
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rcvr['id']

            yield handler.get()

    @inlineCallbacks
    def test_put_data_obtained_with_get(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list()
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rcvr['id']

            yield handler.get()

            handler = self.request(self.responses[0], role='receiver')
            handler.current_user.user_id = rcvr['id']
            yield handler.put()

    @inlineCallbacks
    def test_put_with_remove_pgp_flag_true(self):
        handler = self.request(role='receiver')

        rcvrs = yield admin.get_receiver_list()
        for rcvr in rcvrs:
            handler = self.request(role='receiver')
            handler.current_user.user_id = rcvr['id']

            yield handler.get()

            self.responses[0]['gpg_key_remove'] = True

            handler = self.request(self.responses[0], role='receiver')
            handler.current_user.user_id = rcvr['id']
            yield handler.put()

class TestTipsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.TipsCollection

    @inlineCallbacks
    def test_get(self):
        # FIXME currently the helpers.TestHandlerWithPopulatedDB do not populate any tip
        #       so that very few code is covered. 
        handler = self.request(role='receiver')
        yield handler.get()
