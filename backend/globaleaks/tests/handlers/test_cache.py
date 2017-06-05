# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache
from globaleaks.handlers import public
from globaleaks.tests import helpers


class TestGLApiCache(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        GLApiCache.invalidate()

    def test_get_set_items(self):
        self.assertEqual(GLApiCache.memory_cache_dict, {})
        self.assertIsNone(GLApiCache.get("passante_di_professione", "it"))
        self.assertIsNone(GLApiCache.get("passante_di_professione", "en"))
        GLApiCache.set("passante_di_professione", "it", 'ititit')
        GLApiCache.set("passante_di_professione", "en", 'enenen')
        self.assertTrue("passante_di_professione" in GLApiCache.memory_cache_dict)
        self.assertTrue("it" in GLApiCache.memory_cache_dict['passante_di_professione'])
        self.assertTrue("en" in GLApiCache.memory_cache_dict['passante_di_professione'])
        self.assertEqual(GLApiCache.get("passante_di_professione", "it"), 'ititit')
        self.assertEqual(GLApiCache.get("passante_di_professione", "en"), 'enenen')
        GLApiCache.invalidate("passante_di_professione")
        self.assertEqual(GLApiCache.memory_cache_dict, {})


class TestCacheWithHandlers(helpers.TestHandlerWithPopulatedDB):
    _handler = public.PublicResource

    @inlineCallbacks
    def test_handler_cache_hit(self):
        GLApiCache.invalidate('public')
        handler = self.request()
        response = yield handler.get()

        self.assertEqual(len(GLApiCache.memory_cache_dict), 1)

        GLApiCache.get("public")
        # TODO assert that the cache is placed. 

    @inlineCallbacks
    def test_handler_cache_miss(self):
        # TODO assert that when an async get is fired the cache is filled
        # also assert that when a sync response fills the cache fills it
        pass
