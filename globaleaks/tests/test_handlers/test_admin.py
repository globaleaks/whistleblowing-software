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
        handler = self.request(self.dummyNode)
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.put()
        del self.dummyNode['password']
        del self.dummyNode['old_password']
        self.responses[0]['notification_settings'] = {}
        self.assertEqual(self.responses[0], self.dummyNode)

class TestContextsCollection(helpers.TestHandler):
    _handler = admin.ContextsCollection

    def test_get(self):
        handler = self.request()
        handler.request.headers['X-Session'] = 'test_admin'
        return handler.get()

    @inlineCallbacks
    def test_post(self):
        request_context = self.dummyContext
        handler = self.request(request_context)
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.post()

        del request_context['contexts']
        del request_context['context_gus']
        del self.responses[0]['context_gus']
        self.assertEqual(self.responses[0], request_context)

class TestContextInstance(helpers.TestHandler):
    _handler = admin.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request()
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.get(self.dummyContext['context_gus'])
        del self.dummyContext['contexts']
        self.assertEqual(self.responses[0], self.dummyContext)

    @inlineCallbacks
    def test_put(self):
        request_context = self.dummyContext
        request_context['name'] = u'spam'
        handler = self.request(request_context)
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.put(request_context['context_gus'])

        del request_context['contexts']
        self.assertEqual(self.responses[0], self.dummyContext)

class TestReceiversCollection(helpers.TestHandler):
    _handler = admin.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request()
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.get()

        # XXX helpers.py.. Why self.responses is became a double array ?
        del self.dummyReceiver['contexts']
        del self.responses[0][0]['contexts']
        self.assertEqual(self.responses[0][0], self.dummyReceiver)

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver['name'] = 'beppe'
        handler = self.request(self.dummyReceiver)
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.post()

        # We delete this because it's randomly generated
        del self.responses[0]['receiver_gus']
        del self.dummyReceiver['receiver_gus']
        self.assertEqual(self.responses[0], self.dummyReceiver)

class TestReceiverInstance(helpers.TestHandler):
    _handler = admin.ReceiverInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request()
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.get(self.dummyReceiver['receiver_gus'])
        del self.dummyReceiver['contexts']
        del self.responses[0]['contexts']
        self.assertEqual(self.responses[0], self.dummyReceiver)

    @unittest.skip("because the error is currently not trappable")
    @inlineCallbacks
    def test_put(self):
        self.dummyReceiver['context_gus'] = u'invalid'
        handler = self.request(self.dummyReceiver)
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.put(self.dummyReceiver['receiver_gus'])

    @unittest.skip("because the error is currently not trappable")
    @inlineCallbacks
    def test_put_invalid_context_gus(self):
        self.dummyReceiver['name'] = u'spamham'
        self.dummyReceiver['context_gus'] = u'invalid'
        handler = self.request(self.dummyReceiver)
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.put(self.dummyReceiver['receiver_gus'])
        self.assertEqual(self.responses[0], self.dummyReceiver)

    @unittest.skip("because not implemented")
    @inlineCallbacks
    def test_delete(self):
        self.skip()
        handler = self.request(self.dummyReceiver)
        handler.request.headers['X-Session'] = 'test_admin'
        yield handler.delete()
