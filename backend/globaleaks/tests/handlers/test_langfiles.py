# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.handlers import langfiles


class TestLanguageFileHandler(helpers.TestHandler):
    _handler = langfiles.LanguageFileHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request()

        handler = self.request({}, role='admin')

        yield handler.get(lang='en')
