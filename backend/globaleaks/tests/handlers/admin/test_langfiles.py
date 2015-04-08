# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks
from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers.admin import langfiles


class TestLanguageFileHandler(helpers.TestHandler):
    _handler = langfiles.AdminLanguageFileHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request()

        handler = self.request({}, role='admin')

        yield handler.get(lang='en')

    @inlineCallbacks
    def test_post(self):
        request_body = self.get_dummy_file(filename='en.json', content_type='application/json')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post(lang='en')

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.StaticFileDesc)

    def test_delete_not_existent_custom_lang(self):
        handler = self.request({}, role='admin')
        self.assertRaises(errors.LangFileNotFound, handler.delete, lang='en')

    @inlineCallbacks
    def test_delete_existent_custom_lang(self):
        # we load a custom translation for en
        yield self.test_post()

        handler = self.request({}, role='admin')
        handler.delete(lang='en')
