# -*- coding: utf-8 -*-
from globaleaks.handlers import shorturl
from globaleaks.handlers.admin import shorturl as admin_shorturl
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestShortUrlInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortUrlInstance

    @inlineCallbacks
    def test_get_existent_shorturl(self):
        shorturl_desc = self.get_dummy_shorturl()
        shorturl_desc = yield admin_shorturl.create_shorturl(1, shorturl_desc)

        handler = self.request(role='admin')
        yield handler.get(shorturl_desc['shorturl'])

    @inlineCallbacks
    def test_get_nonexistent_shorturl(self):
        handler = self.request(role='admin')
        yield handler.get(u'/s/nonexistent')
