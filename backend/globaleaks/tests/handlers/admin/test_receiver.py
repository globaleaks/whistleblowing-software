# -*- coding: utf-8 -*-

import sqlite3

from globaleaks.handlers.admin import receiver
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.utility import uuid4
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
    def test_put_invalid_context_id(self):
        self.dummyReceiver_1['contexts'] = [unicode(uuid4())]

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']),
                                 sqlite3.IntegrityError)
