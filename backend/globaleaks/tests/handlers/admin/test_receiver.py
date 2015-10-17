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

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver_1['username'] = 'beppe'

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.post()

    @inlineCallbacks
    def test_post_invalid_mail_address(self):
        self.dummyReceiver_1['username'] = 'beppe'
        self.dummyReceiver_1['mail_address'] = "[est@globaleaks.org"

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.post(), InvalidInputFormat)


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
    def test_put_change_name(self):
        self.dummyReceiver_1['name'] = u'new unique name %d' % random.randint(1, 10000)

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.put(self.dummyReceiver_1['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver_1['name'])

    @inlineCallbacks
    def test_put_change_valid_password(self):
        self.dummyReceiver_1['name'] = u'trick to verify the update is accepted'
        self.dummyReceiver_1['password'] = u'12345678antani'

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.put(self.dummyReceiver_1['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver_1['name'])

    @inlineCallbacks
    def test_put_change_invalid_password(self):
        self.dummyReceiver_1['name'] = u'trick to verify the update is accepted'
        self.dummyReceiver_1['password'] = u'toosimplepassword'

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']), InvalidInputFormat)

    @inlineCallbacks
    def test_put_invalid_context_id(self):
        self.dummyReceiver_1['contexts'] = [unicode(uuid4())]

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']),
                                 errors.ContextIdNotFound)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.delete(self.dummyReceiver_1['id'])
        yield self.assertFailure(handler.get(self.dummyReceiver_1['id']),
                                 errors.ReceiverIdNotFound)
