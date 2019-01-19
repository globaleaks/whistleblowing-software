# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.rest.cache import Cache, gzipdata
from globaleaks.tests import helpers


class TestCache(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        Cache.invalidate()

    def test_cache(self):
        self.assertEqual(Cache.memory_cache_dict, {})
        self.assertIsNone(Cache.get(1, "passante_di_professione", "it"))
        self.assertIsNone(Cache.get(1, "passante_di_professione", "en"))
        self.assertIsNone(Cache.get(2, "passante_di_professione", "ca"))
        Cache.set(1, "passante_di_professione", "it", 'text/plain', 'ititit')
        Cache.set(1, "passante_di_professione", "en", 'text/plain', 'enenen')
        Cache.set(2, "passante_di_professione", "ca", 'text/plain', 'cacaca')
        self.assertTrue("passante_di_professione" in Cache.memory_cache_dict[1])
        self.assertTrue("passante_di_professione" in Cache.memory_cache_dict[2])
        self.assertIsNone(Cache.get(1, "passante_di_professione", "ca"))
        self.assertTrue("it" in Cache.memory_cache_dict[1]['passante_di_professione'])
        self.assertTrue("en" in Cache.memory_cache_dict[1]['passante_di_professione'])
        self.assertIsNone(Cache.get(1, "passante_di_professione", "ca"))
        self.assertEqual(Cache.get(1, "passante_di_professione", "it")[1], gzipdata('ititit'))
        self.assertEqual(Cache.get(1, "passante_di_professione", "en")[1], gzipdata('enenen'))
        self.assertEqual(Cache.get(2, "passante_di_professione", "ca")[1], gzipdata('cacaca'))
        Cache.invalidate()
        self.assertEqual(Cache.memory_cache_dict, {})
