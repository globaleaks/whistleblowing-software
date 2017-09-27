# -*- coding: utf-8 -*-

from globaleaks.handlers import robots
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestRobotstxtHandlerHandler(helpers.TestHandler):
    _handler = robots.RobotstxtHandler

    @inlineCallbacks
    def test_get_with_indexing_disabled(self):
        handler = self.request()

        Settings.memory_copy.allow_indexing = False

        response = yield handler.get()

        self.assertEqual(response, "User-agent: *\n"
                                   "Disallow: /")

    @inlineCallbacks
    def test_get_with_indexing_enabled(self):
        handler = self.request()

        Settings.memory_copy.allow_indexing = True
        Settings.memory_copy.hostname = "www.globaleaks.org"

        response = yield handler.get()

        self.assertEqual(response, "User-agent: *\n"
                                   "Allow: /\n"
                                   "Sitemap: https://www.globaleaks.org/sitemap.xml")


class TestSitemapHandlerHandler(helpers.TestHandler):
    _handler = robots.SitemapHandler

    @inlineCallbacks
    def test_get_with_indexing_disabled(self):
        handler = self.request()

        Settings.memory_copy.allow_indexing = False

        yield self.assertRaises(errors.ResourceNotFound, handler.get)

    @inlineCallbacks
    def test_get_with_indexing_enabled(self):
        handler = self.request()

        Settings.memory_copy.allow_indexing = True

        yield handler.get()

        self.assertEqual(handler.request.code, 200)
