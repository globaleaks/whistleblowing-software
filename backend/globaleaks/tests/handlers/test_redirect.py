# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import redirect
from globaleaks.tests import helpers

specials = ['/admin', '/login', '/submission']

class TestSpecialRedirectHandler(helpers.TestHandler):
    _handler = redirect.SpecialRedirectHandler

    @inlineCallbacks
    def test_get(self):
        for special in specials:
            handler = self.request()
            yield handler.get(special)
            self.assertEqual(handler.request.responseHeaders.getRawHeaders('location')[0], '/#' + special)
