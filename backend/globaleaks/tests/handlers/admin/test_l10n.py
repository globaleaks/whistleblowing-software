# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import l10n
from globaleaks.handlers.admin import l10n as admin_l10n

empty_texts = {}

custom_texts = {
   '12345': '54321'
}

class TestAdminL10NHandler(helpers.TestHandler):
    _handler = admin_l10n.AdminL10NHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request(role='admin')

        yield handler.get(lang=u'en')

        self.assertEqual(len(self.responses), 0)

    @inlineCallbacks
    def test_put(self):
        check = yield admin_l10n.get_custom_texts(u'en')
        self.assertEqual(empty_texts, check)

        handler = self.request({}, role='admin', body=json.dumps(custom_texts))

        yield handler.put(lang=u'en')

        check = yield admin_l10n.get_custom_texts(u'en')
        self.assertEqual(custom_texts, check)

    @inlineCallbacks
    def test_delete(self):
        yield self.test_put()

        check = yield admin_l10n.get_custom_texts(u'en')
        self.assertEqual(custom_texts, check)

        handler = self.request({}, role='admin')
        handler.delete(lang=u'en')

        check = yield admin_l10n.get_custom_texts(u'en')
        self.assertEqual(empty_texts, check)
