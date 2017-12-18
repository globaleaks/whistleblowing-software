# -*- coding: utf-8 -*-
from globaleaks.handlers.admin import receiver
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        response = yield handler.get()
        self.assertEqual(len(response), 2)


class TestReceiverInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    @inlineCallbacks
    def test_put(self):
        self.dummyReceiver_1['can_delete_submission'] = False
        handler = self.request(self.dummyReceiver_1, role='admin')

        response = yield handler.put(self.dummyReceiver_1['id'])

        self.assertFalse(response['can_delete_submission'])
