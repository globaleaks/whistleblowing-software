# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import admstaticfiles
from globaleaks.settings import GLSetting
from globaleaks.security import GLSecureTemporaryFile

class TestStaticFileInstance(helpers.TestHandler):
    _handler = admstaticfiles.StaticFileInstance

    @inlineCallbacks
    def test_post_globaleaks_logo(self):

        request_body = self.get_dummy_file(filename='globaleaks_logo.png', content_type='image/png')

        handler = self.request({}, role='admin',  kwargs={'path': GLSetting.static_path}, body=request_body)

        yield handler.post(filename='globaleaks_logo')

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.staticFile)

    @inlineCallbacks
    def test_post_custom_stylesheet(self):

        request_body = self.get_dummy_file(filename='antani.css', content_type='text/css')

        handler = self.request({}, role='admin',  kwargs={'path': GLSetting.static_path}, body=request_body)

        yield handler.post(filename='custom_stylesheet')

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.staticFile)

    @inlineCallbacks
    def test_post_custom_homepage(self):

        request_body = self.get_dummy_file(filename='antani.html', content_type='text/html')

        handler = self.request({}, role='admin',  kwargs={'path': GLSetting.static_path}, body=request_body)

        yield handler.post(filename='custom_homepage')

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.staticFile)


    def test_post_invalid_name(self):
        """
        test against invalid name:
            - no custom file upload
            - no css
            - no logo
            - no receiver picture
        """

        request_body = self.get_dummy_file(filename='valid_customization', content_type='text/plain')

        handler = self.request({}, role='admin',  kwargs={'path': GLSetting.static_path}, body=request_body)
        self.assertFailure(handler.post(filename='invalid.blabla'), errors.ReceiverIdNotFound)

    @inlineCallbacks
    def test_delete_on_existent_file(self):
        handler = self.request({}, role='admin',  kwargs={'path':"globaleaks_logo"})
        yield handler.delete("globaleaks_logo.png")

    def test_delete_on_non_existent_file(self):
        handler = self.request({}, role='admin',  kwargs={'path':"not_existent"})
        self.assertRaises(errors.StaticFileNotFound, handler.delete, filename='not_existent.txt')

    @inlineCallbacks
    def test_post_valid_custom_file(self):
        """
        test against invalid name:
            - no custom file upload
            - no css
            - no logo
            - no receiver picture
        """

        request_body = self.get_dummy_file(filename='valid.blabla', content_type='text/plain')

        handler = self.request({}, role='admin',  kwargs={'path': GLSetting.static_path}, body=request_body)
        yield handler.post(filename='customization')
        self._handler.validate_message(json.dumps(self.responses[0]), requests.staticFile)

    @inlineCallbacks
    def test_delete_valid_custom_file(self):
        # we load a file
        yield self.test_post_valid_custom_file()

        # we delete the file
        handler = self.request({}, role='admin', kwargs={'path': GLSetting.static_path})
        yield handler.delete("valid.blabla")

        # we verify that the file do not exists anymore
        handler = self.request({}, role='admin', kwargs={'path': GLSetting.static_path})
        self.assertRaises(errors.StaticFileNotFound, handler.delete, filename='validblabla')


class TestStaticFileList(helpers.TestHandler):
    _handler = admstaticfiles.StaticFileList

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 5)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.staticFileCollection)
