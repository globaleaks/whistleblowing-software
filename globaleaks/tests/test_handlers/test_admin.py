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
        return handler.get()

    @inlineCallbacks
    def test_put_update_node(self):
        handler = self.request(self.dummyNode)
        yield handler.put()
        del self.dummyNode['password']
        del self.dummyNode['old_password']
        self.assertEqual(self.responses[0], self.dummyNode)

class TestContextsCollection(helpers.TestHandler):
    _handler = admin.ContextsCollection

    def test_get(self):
        handler = self.request()
        return handler.get()

    @inlineCallbacks
    def test_post(self):
        handler = self.request(self.dummyContext)
        yield handler.post()
        del self.responses[0]['context_gus']
        del self.dummyContext['context_gus']

        self.assertEqual(self.responses[0], self.dummyContext)

class TestContextInstance(helpers.TestHandler):
    _handler = admin.ContextInstance

    @inlineCallbacks
    def test_get(self):
        handler = self.request()
        yield handler.get(self.dummyContext['context_gus'])
        self.assertEqual(self.responses[0], self.dummyContext)

    @inlineCallbacks
    def test_put(self):
        self.dummyContext['name'] = u'spam'
        handler = self.request(self.dummyContext)
        yield handler.put(self.dummyContext['context_gus'])
        self.assertEqual(self.responses[0], self.dummyContext)

class TestReceiversCollection(helpers.TestHandler):
    _handler = admin.ReceiversCollection

    @inlineCallbacks
    def test_get(self):
        handler = self.request()
        handler.request.headers['X-Session'] = self.login('admin')
        yield handler.get()
        self.assertEqual(self.responses[0], [self.dummyReceiver])

    @inlineCallbacks
    def test_post(self):
        self.dummyReceiver['name'] = 'beppe'
        handler = self.request(self.dummyReceiver)
        handler.request.headers['X-Session'] = self.login('admin')
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
        yield handler.get(self.dummyReceiver['receiver_gus'])
        self.assertEqual(self.responses[0], self.dummyReceiver)

    @unittest.skip("because the error is currently not trappable")
    @inlineCallbacks
    def test_put(self):
        self.dummyReceiver['context_gus'] = u'invalid'
        handler = self.request(self.dummyReceiver)
        yield handler.put(self.dummyReceiver['receiver_gus'])

    @unittest.skip("because the error is currently not trappable")
    @inlineCallbacks
    def test_put_invalid_context_gus(self):
        self.dummyReceiver['name'] = u'spamham'
        self.dummyReceiver['context_gus'] = u'invalid'
        handler = self.request(self.dummyReceiver)
        yield handler.put(self.dummyReceiver['receiver_gus'])
        self.assertEqual(self.responses[0], self.dummyReceiver)

    @unittest.skip("because not implemented")
    @inlineCallbacks
    def test_delete(self):
        self.skip()
        handler = self.request(self.dummyReceiver)
        yield handler.delete()

class TestPluginCollection(helpers.TestHandler):
    _handler = admin.PluginCollection
    pass

class TestStatisticsCollection(helpers.TestHandler):
    _handler = admin.StatisticsCollection
    pass
