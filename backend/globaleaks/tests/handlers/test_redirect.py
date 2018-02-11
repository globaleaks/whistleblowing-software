# -*- coding: utf-8 -*-
from globaleaks.handlers import redirect
from globaleaks.state import State
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestRedirectLogin():
    _handler = redirect.LoginHandler

    @inlineCallbacks
    def test_get_login_redirect(self):
        handler = self.request(role='*')
        yield handler.get(u'/login')
        location = request.responseHeaders.getRawHeaders(b'location')[0]
        self.assertEqual('/#/login', location)
