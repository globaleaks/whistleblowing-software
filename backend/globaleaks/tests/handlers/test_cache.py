# -*- coding: utf-8 -*-
from random import randint

from globaleaks import handlers
from globaleaks.handlers import public
from globaleaks.rest.apicache import ApiCache, decorator_cache_get
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestApiCache(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        ApiCache.invalidate()

    def test_get_set_items(self):
        self.assertEqual(ApiCache.memory_cache_dict, {})
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "it"))
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "en"))
        self.assertIsNone(ApiCache.get(2, "passante_di_professione", "ca"))
        ApiCache.set(1, "passante_di_professione", "it", 'ititit')
        ApiCache.set(1, "passante_di_professione", "en", 'enenen')
        ApiCache.set(2, "passante_di_professione", "ca", 'cacaca')
        self.assertTrue("passante_di_professione" in ApiCache.memory_cache_dict[1])
        self.assertTrue("passante_di_professione" in ApiCache.memory_cache_dict[2])
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "ca"))
        self.assertTrue("it" in ApiCache.memory_cache_dict[1]['passante_di_professione'])
        self.assertTrue("en" in ApiCache.memory_cache_dict[1]['passante_di_professione'])
        self.assertIsNone(ApiCache.get(1, "passante_di_professione", "ca"))
        self.assertEqual(ApiCache.get(1, "passante_di_professione", "it"), 'ititit')
        self.assertEqual(ApiCache.get(1, "passante_di_professione", "en"), 'enenen')
        self.assertEqual(ApiCache.get(2, "passante_di_professione", "ca"), 'cacaca')
        ApiCache.invalidate()
        self.assertEqual(ApiCache.memory_cache_dict, {})


class TestCacheWithHandlers(helpers.TestHandler):
    _handler = public.PublicResource

    @inlineCallbacks
    def test_handler_cache_hit(self):
        ApiCache.invalidate()

        handler = self.request(uri='https://www.globaleaks.org/public')
        resp = yield handler.get()

        self.assertEqual(len(ApiCache.memory_cache_dict), 1)

        cached_resp = ApiCache.get(1, "/public", "en")

        second_resp = yield handler.get()
        self.assertEqual(resp, cached_resp)
        self.assertEqual(resp, second_resp)

        # Check that a different language doesn't blow away a different resource
        handler_fr = self.request(uri='https://www.globaleaks.org/public', headers={'gl-language': 'fr'})
        resp_fr = yield handler_fr.get()
        cached_resp_fr = ApiCache.get(1, "/public", "fr")

        self.assertEqual(resp_fr, cached_resp_fr)


        s = reduce(lambda x, y: x+len(y), ApiCache.memory_cache_dict[1].values(), 0)

        self.assertEqual(s, 2)
        self.assertNotEqual(resp_fr, cached_resp)

    def test_handler_sync_cache_miss(self):
        # Asserts that the cases where the result of f returns immediately,
        # the caching implementation does not fall over and die.
        ApiCache.invalidate()

        fake_path = '/xxx'
        fake_uri = 'https://www.globaleaks.org' + fake_path
        handler = self.request(handler_cls=FakeSyncHandler, uri=fake_uri)
        resp = handler.get()

        cached_resp = ApiCache.get(1, fake_path, "en")

        second_resp = handler.get()
        self.assertEqual(resp, cached_resp)
        self.assertEqual(resp, second_resp)


class FakeSyncHandler(handlers.base.BaseHandler):
    check_roles='*'

    @decorator_cache_get
    def get(self):
        return {'meta': randint(0, 1e6)}
