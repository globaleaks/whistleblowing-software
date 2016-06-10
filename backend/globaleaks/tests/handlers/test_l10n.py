# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import l10n
from globaleaks.handlers.admin import l10n as admin_l10n

custom_texts = {
   '12345': '54321'
}

class TestL10NHandler(helpers.TestHandler):
    _handler = l10n.L10NHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request()

        yield handler.get(lang=u'en')

        self.assertNotIn('12345', self.responses[0])

        yield admin_l10n.update_custom_texts(u'en', custom_texts)

        yield handler.get(lang=u'en')

        self.assertIn('12345', self.responses[1])
        self.assertEqual('54321', self.responses[1]['12345'])
