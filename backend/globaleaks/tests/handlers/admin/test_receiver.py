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

# special guest:

stuff = u"³²¼½¬¼³²"


class TestReceiversCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        self.assertEqual(len(self.responses[0]), 2)


class TestReceiverCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = receiver.ReceiverCreate

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver_1['name'] = 'beppe'

        self.dummyReceiver_1['mail_address'] =  "test@globaleaks.org"
        self.dummyReceiver_1['password'] = helpers.VALID_PASSWORD1

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.post()

    @inlineCallbacks
    def test_post_invalid_mail_address(self):
        self.dummyReceiver_1['name'] = 'beppe'
        self.dummyReceiver_1['mail_address'] = "[est@globaleaks.org"
        self.dummyReceiver_1['password'] = helpers.VALID_PASSWORD1

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

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
        self.dummyReceiver_1['context_id'] = ''
        self.dummyReceiver_1['name'] = u'new unique name %d' % random.randint(1, 10000)

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.put(self.dummyReceiver_1['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver_1['name'])

    @inlineCallbacks
    def test_put_change_valid_password(self):
        self.dummyReceiver_1['context_id'] = ''
        self.dummyReceiver_1['name'] = u'trick to verify the update is accepted'
        self.dummyReceiver_1['password'] = u'12345678antani'

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.put(self.dummyReceiver_1['id'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver_1['name'])

    @inlineCallbacks
    def test_put_change_invalid_password(self):
        self.dummyReceiver_1['context_id'] = ''
        self.dummyReceiver_1['name'] = u'trick to verify the update is accepted'
        self.dummyReceiver_1['password'] = u'toosimplepassword'

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')
        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']), InvalidInputFormat)

    @inlineCallbacks
    def test_put_invalid_context_id(self):
        self.dummyReceiver_1['name'] = u'justalazyupdate'
        self.dummyReceiver_1['contexts'] = [unicode(uuid4())]
        self.dummyReceiver_1['name'] = u'another unique name %d' % random.randint(1, 10000)
        self.dummyReceiver_1['mail_address'] = u'but%d@random.id' % random.randint(1, 1000)
        self.dummyReceiver_1['password'] = u'12345678andaletter'

        for attrname in Receiver.localized_strings:
            self.dummyReceiver_1[attrname] = stuff

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']),
                                 errors.ContextIdNotFound)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyReceiver_1, role='admin')
        yield handler.delete(self.dummyReceiver_1['id'])
        yield self.assertFailure(handler.get(self.dummyReceiver_1['id']),
                                 errors.ReceiverIdNotFound)
