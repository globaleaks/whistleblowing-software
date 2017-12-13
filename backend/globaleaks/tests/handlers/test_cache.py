# -*- coding: utf-8 -*-
from random import randint

from globaleaks import handlers
from globaleaks.handlers import public
from globaleaks.rest.apicache import ApiCache, decorator_cache_get, gzipdata
from globaleaks.state import State
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestApiCache(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        ApiCache.invalidate()

    def test_cache(self):
        self.assertEqual(ApiCache.memory_cache_dict, {})
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "it"))
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "en"))
        self.assertIsNone(ApiCache.get(2, "passante_di_professione", "ca"))
        ApiCache.set(1, "passante_di_professione", "it", 'text/plain', 'ititit')
        ApiCache.set(1, "passante_di_professione", "en", 'text/plain', 'enenen')
        ApiCache.set(2, "passante_di_professione", "ca", 'text/plain', 'cacaca')
        self.assertTrue("passante_di_professione" in ApiCache.memory_cache_dict[1])
        self.assertTrue("passante_di_professione" in ApiCache.memory_cache_dict[2])
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "ca"))
        self.assertTrue("it" in ApiCache.memory_cache_dict[1]['passante_di_professione'])
        self.assertTrue("en" in ApiCache.memory_cache_dict[1]['passante_di_professione'])
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "ca"))
        self.assertEqual(ApiCache.get(1, "passante_di_professione", "it")[1], gzipdata('ititit'))
        self.assertEqual(ApiCache.get(1, "passante_di_professione", "en")[1], gzipdata('enenen'))
        self.assertEqual(ApiCache.get(2, "passante_di_professione", "ca")[1], gzipdata('cacaca'))
        ApiCache.invalidate()
        self.assertEqual(ApiCache.memory_cache_dict, {})
