from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers

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

# class TestReceiversCollection(helpers.TestHandler):
#     _handler = admin.ReceiversCollection
#     def test_get(self):
#         handler = self.request()
#         return handler.get()
# 
#     def test_post(self):
#         handler = self.request()
#         return handler.post()
# 
# class TestReceiverInstance(helpers.TestHandler):
#     _handler = admin.ReceiverInstance
#     def test_get(self):
#         handler = self.request()
#         return handler.get()
# 
#     def test_put(self):
#         handler = self.request()
#         return handler.put()
# 
#     def test_delete(self):
#         handler = self.request()
#         return handler.delete()
# 
# class TestPluginCollection(helpers.TestHandler):
#     _handler = admin.PluginCollection
#     pass
# 
# class TestStatisticsCollection(helpers.TestHandler):
#     _handler = admin.StatisticsCollection
#     pass
