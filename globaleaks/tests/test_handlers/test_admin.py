import time
import unittest
from cyclone.util import ObjectDict as OD

from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.rest import errors

from globaleaks import settings
from globaleaks.handlers import admin

class TestNodeInstance(helpers.TestHandler):
    _handler = admin.NodeInstance

    def test_get(self):
        handler = self.request({})
        handler.request.headers['X-Session'] = 'test_admin'
        return handler.get()

    @inlineCallbacks
    def test_put_update_node(self):
        handler = self.request(self.dummyNode, role='admin')
        yield handler.put()
        del self.dummyNode['password']
        del self.dummyNode['old_password']
        del self.responses[0]['notification_settings']
        del self.dummyNode['notification_settings']
        self.assertEqual(self.responses[0], self.dummyNode)

class TestContextsCollection(helpers.TestHandler):
    _handler = admin.ContextsCollection

    def test_get(self):
        handler = self.request(role='admin')
        handler.request.headers['X-Session'] = 'test_admin'
        return handler.get()

    @inlineCallbacks
    def test_post(self):
        request_context = self.dummyContext
        del request_context['contexts'] # why is here !?
        handler = self.request(request_context, role='admin')
        yield handler.post()

        request_context['context_gus'] =  self.responses[0]['context_gus']
        self.assertEqual(self.responses[0], request_context)

class TestContextInstance(helpers.TestHandler):
    _handler = admin.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyContext['context_gus'])
        del self.dummyContext['contexts']
        self.assertEqual(self.responses[0], self.dummyContext)

    @inlineCallbacks
    def test_put(self):
        request_context = self.dummyContext
        request_context['name'] = u'spam'
        del request_context['contexts'] # I don't know what's doing here!!?
        handler = self.request(request_context, role='admin')
        yield handler.put(request_context['context_gus'])
        self.assertEqual(self.responses[0], self.dummyContext)

class TestReceiversCollection(helpers.TestHandler):
    _handler = admin.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get()

        # XXX helpers.py.. Why self.responses is became a double array ?
        del self.dummyReceiver['contexts']
        del self.responses[0][0]['contexts']
        self.assertEqual(self.responses[0][0], self.dummyReceiver)

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver['name'] = 'beppe'
        handler = self.request(self.dummyReceiver, role='admin')
        yield handler.post()

        # We delete this because it's randomly generated
        del self.responses[0]['receiver_gus']
        del self.dummyReceiver['receiver_gus']
        self.assertEqual(self.responses[0], self.dummyReceiver)

class TestReceiverInstance(helpers.TestHandler):
    _handler = admin.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')
        yield handler.get(self.dummyReceiver['receiver_gus'])
        del self.dummyReceiver['contexts']
        del self.responses[0]['contexts']
        self.assertEqual(self.responses[0], self.dummyReceiver)

    @inlineCallbacks
    def test_put(self):
        self.dummyReceiver['context_gus'] = ''
        del self.dummyReceiver['username']
        self.dummyReceiver['name'] = u'new name'
        handler = self.request(self.dummyReceiver, role='admin')
        yield handler.put(self.dummyReceiver['receiver_gus'])
        self.assertEqual(self.responses[0]['name'], self.dummyReceiver['name'])

    @inlineCallbacks
    def test_put_invalid_context_gus(self):
        self.dummyReceiver['name'] = u'justalazyupdate'
        # keep the context_gus wrong but matching eventually regexp
        import uuid
        self.dummyReceiver['contexts'] = [ unicode(uuid.uuid4()) ]
        handler = self.request(self.dummyReceiver, role='admin')
        # I've some issue in use assertRaises with 'yield', then:
        try:
            yield handler.put(self.dummyReceiver['receiver_gus'])
            self.assertTrue(False)
        except errors.ContextGusNotFound:
            self.assertTrue(True)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request(self.dummyReceiver, role='admin')
        try:
            yield handler.delete(self.dummyReceiver['receiver_gus'])
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
        try:
            yield handler.get(self.dummyReceiver['receiver_gus'])
            self.assertTrue(False)
        except errors.ReceiverGusNotFound:
            self.assertTrue(True)

