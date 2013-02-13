from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers

from globaleaks.handlers import admin

class TestNodeInstance(helpers.TestHandler):
    _handler = admin.NodeInstance

    # def setUp(self):
    #     pass

    # def tearDown(self):
    #     pass

    def test_get(self):
        handler = self.request({})
        d = handler.get()
        return d

    # def test_put(self):
    #     handler = self.request({})
    #     return handler.put()
# 
# class TestContextsCollection(helpers.TestHandler):
#     _handler = admin.ContextsCollection
# 
#     def test_get(self):
#         handler = self.request()
#         return handler.get()
# 
#     def test_post(self):
#         handler = self.request()
#         return handler.post()
# 
# class TestContextInstance(helpers.TestHandler):
#     _handler = admin.ContextInstance
#     def test_get(self):
#         handler = self.request()
#         return handler.get()
# 
#     def test_post(self):
#         handler = self.request()
#         return handler.post()
# 
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
