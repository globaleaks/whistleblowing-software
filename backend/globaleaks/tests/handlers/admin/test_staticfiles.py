# -*- coding: utf-8 -*-

import os

from globaleaks.handlers.admin import staticfiles
from globaleaks.handlers.base import write_upload_plaintext_to_disk
from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestStaticFileInstance(helpers.TestHandler):
    _handler = staticfiles.StaticFileInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post(filename='img.png')

    @inlineCallbacks
    def test_delete_on_existent_file(self):
        self.fakeFile = self.get_dummy_file()
        realpath = os.path.join(GLSettings.static_path, self.fakeFile['name'])
        yield write_upload_plaintext_to_disk(self.fakeFile, realpath)

        handler = self.request({}, role='admin')
        yield handler.delete(self.fakeFile['name'])

    def test_delete_non_existent_file(self):
        handler = self.request({}, role='admin')
        self.assertRaises(errors.StaticFileNotFound, handler.delete, filename='not_existent.txt')


class TestStaticFileList(helpers.TestHandler):
    _handler = staticfiles.StaticFileList

    @inlineCallbacks
    def test_get_list_of_files(self):
        self.fakeFile = self.get_dummy_file()
        realpath = os.path.join(GLSettings.static_path, self.fakeFile['name'])
        yield write_upload_plaintext_to_disk(self.fakeFile, realpath)

        handler = self.request(role='admin')
        response = yield handler.get()

        found = False
        for f in response:
            if f['name'] == self.fakeFile['name']:
                found = True
                break

        self.assertTrue(found)
