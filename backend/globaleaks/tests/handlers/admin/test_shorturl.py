# -*- coding: utf-8 -*-

from globaleaks.handlers.admin import shorturl
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestShortURLCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortURLCollection

    @inlineCallbacks
    def test_get(self):
        for i in range(3):
            yield shorturl.create_shorturl(helpers.XTIDX, self.get_dummy_shorturl(str(i)))

        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 3)

    @inlineCallbacks
    def test_post_new_shorturl(self):
        shorturl_desc = self.get_dummy_shorturl()
        handler = self.request(shorturl_desc, role='admin')
        yield handler.post()


class TestShortURLInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortURLInstance

    @inlineCallbacks
    def test_delete(self):
        shorturl_desc = self.get_dummy_shorturl()
        shorturl_desc = yield shorturl.create_shorturl(helpers.XTIDX, shorturl_desc)

        handler = self.request(role='admin')
        yield handler.delete(shorturl_desc['id'])
