# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import site
from globaleaks.tests import helpers


class TestSiteListResource(helpers.TestHandlerWithPopulatedDB):
    _handler = site.SiteCollection

    @inlineCallbacks
    def test_get_with_multisite_login_off(self):
        handler = self.request()
        response = yield handler.get()
        self.assertEqual(len(response), 0)

    @inlineCallbacks
    def test_get_with_multisite_login_on(self):
        self.state.tenant_cache[1].multisite_login = True
        handler = self.request()
        response = yield handler.get()
        self.assertEqual(len(response), 3)
