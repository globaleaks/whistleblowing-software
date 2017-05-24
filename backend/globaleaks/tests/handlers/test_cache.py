# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache
from globaleaks.tests import helpers


class TestGLApiCache(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        GLApiCache.invalidate()

    def test_apicache(self):
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
