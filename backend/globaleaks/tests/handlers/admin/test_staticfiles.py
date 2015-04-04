# -*- coding: utf-8 -*-
from io import BytesIO as StringIO

from twisted.internet.defer import inlineCallbacks
import os
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.handlers.admin import staticfiles
from globaleaks.settings import GLSetting


class TestStaticFileInstance(helpers.TestHandler):
    _handler = staticfiles.StaticFileInstance

    crappyjunk =  "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

    fakeFile = dict()
    fakeFile['body'] = StringIO()
    fakeFile['body'].write(crappyjunk)
    fakeFile['body_len'] = len(crappyjunk)
    fakeFile['content_type'] = 'image/jpeg'
    fakeFile['filename'] = 'imag0005.jpg'

    @inlineCallbacks
    def test_file_delete_it(self):
        realpath = os.path.join(GLSetting.static_path, self.fakeFile['filename'])
        dumped_file = yield staticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue('filelocation' in dumped_file)

        self.responses = []

        handler = self.request(role='admin')
        yield handler.delete(self.fakeFile['filename'])

    @inlineCallbacks
    def test_post_globaleaks_logo(self):

        request_body = self.get_dummy_file(filename='globaleaks_logo.png', content_type='image/png')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post(filename='globaleaks_logo')

    @inlineCallbacks
    def test_post_custom_stylesheet(self):

        request_body = self.get_dummy_file(filename='antani.css', content_type='text/css')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post(filename='custom_stylesheet')

    @inlineCallbacks
    def test_post_custom_homepage(self):

        request_body = self.get_dummy_file(filename='antani.html', content_type='text/html')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post(filename='custom_homepage')

    def test_post_invalid_name(self):
        """
        test against invalid name:
            - no custom file upload
            - no css
            - no logo
            - no receiver picture
        """

        request_body = self.get_dummy_file(filename='valid_customization', content_type='text/plain')

        handler = self.request({}, role='admin', body=request_body)
        self.assertFailure(handler.post(filename='invalid.blabla'), errors.ReceiverIdNotFound)

    @inlineCallbacks
    def test_delete_on_existent_file(self):
        handler = self.request({}, role='admin')
        yield handler.delete("globaleaks_logo.png")

    def test_delete_on_non_existent_file(self):
        handler = self.request({}, role='admin')
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

        handler = self.request({}, role='admin',  body=request_body)
        yield handler.post(filename='customization')

    @inlineCallbacks
    def test_delete_valid_custom_file(self):
        # we load a file
        yield self.test_post_valid_custom_file()

        # we delete the file
        handler = self.request({}, role='admin')
        yield handler.delete("valid.blabla")

        # we verify that the file do not exists anymore
        handler = self.request({}, role='admin')
        self.assertRaises(errors.StaticFileNotFound, handler.delete, filename='validblabla')


class TestStaticFileList(helpers.TestHandler):
    """
    """
    _handler = staticfiles.StaticFileList

    crappyjunk =  "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

    # default files not filtered from get(/) handler
    default_files = [ 'globaleaks_logo.png',
                      'favicon.ico',
                      'robots.txt',
                      'default-profile-picture.png',
                      'custom_stylesheet.css']

    fakeFile = dict()
    fakeFile['body'] = StringIO()
    fakeFile['body'].write(crappyjunk)
    fakeFile['body_len'] = len(crappyjunk)
    fakeFile['content_type'] = 'image/jpeg'
    fakeFile['filename'] = 'imag0005.jpg'

    @inlineCallbacks
    def test_get_default_staticfile_list(self):
        handler = self.request(role='admin')
        yield handler.get()
        self.assertTrue( isinstance(self.responses[0], list) )

        # this check verifies that only not filtered default files are shown
        # other files shall be present and are ignored in this test
        files_dict = {}

        for f in self.responses[0]:
            files_dict[f['filename']] = f['size']

        for system_names in self.default_files:
            self.assertTrue(system_names in files_dict.keys())


    @inlineCallbacks
    def test_get_list_with_one_custom_file(self):
        realpath = os.path.join(GLSetting.static_path, self.fakeFile['filename'])
        dumped_file = yield staticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue('filelocation' in dumped_file)

        handler = self.request(role='admin')
        yield handler.get()
        self.assertTrue( isinstance(self.responses[0], list) )

        found = False

        for f in self.responses[0]:
            if f['filename'] == self.fakeFile['filename']:
                found = True
                self.assertEqual(self.fakeFile['body_len'], f['size'])

        self.assertTrue(found)
