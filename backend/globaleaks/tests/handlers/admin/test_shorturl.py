# -*- coding: utf-8 -*-
import random

from twisted.internet.defer import inlineCallbacks

from globaleaks import __version__
from globaleaks.rest.errors import InvalidInputFormat
from globaleaks.tests import helpers
from globaleaks.rest import requests, errors
from globaleaks.handlers.admin import shorturl
from globaleaks.models import ShortURL

class TesShortURLCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortURLCollection

    @inlineCallbacks
    def test_get(self):
        for i in range(3):
            yield shorturl.create_shorturl(self.get_dummy_shorturl(str(i)))

        handler = self.request(role='admin')
        yield handler.get()

        self.assertEqual(len(self.responses[0]), 3)

    @inlineCallbacks
    def test_post_new_shorturl(self):
        shorturl_desc = self.get_dummy_shorturl()
        handler = self.request(shorturl_desc, role='admin')
        yield handler.post()

class TesShortURLInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = shorturl.ShortURLInstance

    @inlineCallbacks
    def test_delete(self):
        shorturl_desc = self.get_dummy_shorturl()
        shorturl_desc = yield shorturl.create_shorturl(shorturl_desc)

        handler = self.request(role='admin')
        yield handler.delete(shorturl_desc['id'])
