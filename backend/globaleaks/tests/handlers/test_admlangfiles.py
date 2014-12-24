# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import admlangfiles
from globaleaks.settings import GLSetting
from globaleaks.security import GLSecureTemporaryFile

class TestLanguageFileHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = admlangfiles.LanguageFileHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, kwargs={'path': GLSetting.static_path})
        yield handler.get(lang='en')

    @inlineCallbacks
    def test_post(self):

        temporary_file = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        temporary_file.write("ANTANI")
        temporary_file.avoid_delete()

        request_body = {
            'body': temporary_file,
            'body_len': len("ANTANI"),
            'body_filepath': temporary_file.filepath,
            'filename': 'en.json',
            'content_type': 'application/json'
        }

        handler = self.request({}, role='admin', kwargs={'path': GLSetting.static_path}, body=request_body)

        yield handler.post(lang='en')

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.staticFile)

    @inlineCallbacks
    def test_get_custom_translation(self):
 
        handler = self.request({}, kwargs={'path': GLSetting.static_path})
        yield handler.get(lang='en')

        first_response = self.responses[0]

        self.responses = []

        # we load a custom translation for en
        yield self.test_post()

        self.responses = []

        handler = self.request({}, kwargs={'path': GLSetting.static_path})
        yield handler.get(lang='en')

        self.assertNotEqual(self.responses[0], first_response)

    def test_delete_not_existent_custom_lang(self):
        handler = self.request({}, role='admin', kwargs={'path': GLSetting.static_path})
        self.assertRaises(errors.LangFileNotFound, handler.delete, lang='en')

    @inlineCallbacks
    def test_delete_existent_custom_lang(self):

        # we load a custom translation for en
        yield self.test_post()

        handler = self.request({}, role='admin', kwargs={'path': GLSetting.static_path})
        handler.delete(lang='en')
