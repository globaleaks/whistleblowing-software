# -*- coding: utf-8 -*-
from globaleaks import handlers
from globaleaks.handlers import public
from globaleaks.rest.apicache import GLApiCache, decorator_cache_get
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


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
        GLApiCache.invalidate()
        self.assertEqual(GLApiCache.memory_cache_dict, {})


class TestCacheWithHandlers(helpers.TestHandler):
    _handler = public.PublicResource

    @inlineCallbacks
    def test_handler_cache_hit(self):
        GLApiCache.invalidate()

        handler = self.request(uri='https://www.globaleaks.org/public')
        resp = yield handler.get()

        self.assertEqual(len(GLApiCache.memory_cache_dict), 1)

        cached_resp = GLApiCache.get("/public", "en")

        second_resp = yield handler.get()
        self.assertEqual(resp, cached_resp)
        self.assertEqual(resp, second_resp)

        # Check that a different language doesn't blow away a different resource
        handler_fr = self.request(uri='https://www.globaleaks.org/public', headers={'gl-language': 'fr'})
        resp_fr = yield handler_fr.get()
        cached_resp_fr = GLApiCache.get("/public", "fr")

        self.assertEqual(resp_fr, cached_resp_fr)


        s = reduce(lambda x, y: x+len(y), GLApiCache.memory_cache_dict.values(), 0)

        self.assertEqual(s, 2)
        self.assertNotEqual(resp_fr, cached_resp)

    def test_handler_sync_cache_miss(self):
        # Asserts that the cases where the result of f returns immediately,
        # the caching implementation does not fall over and die.
        GLApiCache.invalidate()

        fake_path = '/xxx'
        fake_uri = 'https://www.globaleaks.org' + fake_path
        handler = self.request(handler_cls=FakeSyncHandler, uri=fake_uri)
        resp = handler.get()

        cached_resp = GLApiCache.get(fake_path, "en")

        second_resp = handler.get()
        self.assertEqual(resp, cached_resp)
        self.assertEqual(resp, second_resp)


class FakeSyncHandler(handlers.base.BaseHandler):
    check_roles='*'

    @decorator_cache_get
    def get(self):
        return {'meta': 'fa paura'}
