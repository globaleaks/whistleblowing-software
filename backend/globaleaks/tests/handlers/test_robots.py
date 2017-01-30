# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import robots
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers


class TestRobotstxtHandlerHandler(helpers.TestHandler):
    _handler = robots.RobotstxtHandler

    @inlineCallbacks
    def test_get_with_indexing_disabled(self):
        handler = self.request()

        GLSettings.memory_copy.allow_indexing = False

        yield handler.get()

        self.assertEqual(self.responses[0], "User-agent: *\n")
        self.assertEqual(self.responses[1], "Disallow: /")

    @inlineCallbacks
    def test_get_with_indexing_enabled(self):
        handler = self.request()

        GLSettings.memory_copy.allow_indexing = True
        GLSettings.memory_copy.public_site = "https://www.globaleaks.org"

        yield handler.get()

        self.assertEqual(self.responses[0], "User-agent: *\n")
        self.assertEqual(self.responses[1], "Allow: /\n")
        self.assertEqual(self.responses[2], "Sitemap: https://www.globaleaks.org/sitemap.xml")


class TestSitemapHandlerHandler(helpers.TestHandler):
    _handler = robots.SitemapHandler

    @inlineCallbacks
    def test_get_with_indexing_disabled(self):
        handler = self.request()

        GLSettings.memory_copy.allow_indexing = False

        yield handler.get()

        self.assertEqual(handler.get_status(), 404)

    @inlineCallbacks
    def test_get_with_indexing_enabled(self):
        handler = self.request()

        GLSettings.memory_copy.allow_indexing = True

        yield handler.get()

        self.assertEqual(handler.get_status(), 200)
