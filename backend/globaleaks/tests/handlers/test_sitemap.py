# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import sitemap
from globaleaks.rest import errors
from globaleaks.state import State
from globaleaks.tests import helpers


class TestSitemapHandlerHandler(helpers.TestHandler):
    _handler = sitemap.SitemapHandler

    def test_get_with_indexing_disabled(self):
        handler = self.request()

        State.tenant_cache[1].allow_indexing = False

        return self.assertRaises(errors.ResourceNotFound, handler.get)

    @inlineCallbacks
    def test_get_with_indexing_enabled(self):
        handler = self.request()

        State.tenant_cache[1].allow_indexing = True

        yield handler.get()

        self.assertEqual(handler.request.code, 200)
