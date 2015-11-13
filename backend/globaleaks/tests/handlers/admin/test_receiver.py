# -*- coding: utf-8 -*-
import random

from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import requests, errors
from globaleaks.handlers.admin import receiver
from globaleaks.models import Receiver
from globaleaks.utils.utility import uuid4


class TestReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.assertEqual(len(self.responses[0]), 2)


class TestReceiverInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyReceiver_1['id'])
        del self.dummyReceiver_1['contexts']
        del self.responses[0]['contexts']
        self.assertEqual(self.responses[0]['id'], self.dummyReceiver_1['id'])

    @inlineCallbacks
    def test_put_invalid_context_id(self):
        self.dummyReceiver_1['contexts'] = [unicode(uuid4())]

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']),
                                 errors.ContextIdNotFound)
