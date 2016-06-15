# -*- coding: utf-8 -*-
from io import BytesIO as StringIO

from twisted.internet.defer import inlineCallbacks
import os
from globaleaks import models
from globaleaks.orm import transact_ro
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.handlers.admin import staticfiles
from globaleaks.settings import GLSettings


class TestStaticFileInstance(helpers.TestHandler):
    _handler = staticfiles.StaticFileInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post(filename='img.png')

    @inlineCallbacks
    def test_delete_on_existent_file(self):
        self.fakeFile = self.get_dummy_file(filename='img.png', content_type='image/png')
        realpath = os.path.join(GLSettings.static_path, self.fakeFile['filename'])
        dumped_file = yield staticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue('filelocation' in dumped_file)

        handler = self.request({}, role='admin')
        yield handler.delete(self.fakeFile['filename'])

    def test_delete_non_existent_file(self):
        handler = self.request({}, role='admin')
        self.assertRaises(errors.StaticFileNotFound, handler.delete, filename='not_existent.txt')


class TestStaticFileList(helpers.TestHandler):
    _handler = staticfiles.StaticFileList

    @inlineCallbacks
    def test_get_list_of_files(self):
        self.fakeFile = self.get_dummy_file()
        realpath = os.path.join(GLSettings.static_path, self.fakeFile['filename'])
        dumped_file = yield staticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue('filelocation' in dumped_file)

        handler = self.request(role='admin')
        yield handler.get()
        self.assertTrue(isinstance(self.responses[0], list))

        found = False

        for f in self.responses[0]:
            if f['filename'] == self.fakeFile['filename']:
                found = True
                break

        self.assertTrue(found)


class TestNodeLogoInstance(helpers.TestHandler):
    key = u'logo'
    _handler = staticfiles.NodeLogoInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post()

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete()

        img = yield staticfiles.get_file(self.key)
        self.assertEqual(img, '')


class TestNodeCSSInstance(TestNodeLogoInstance):
    key = u'custom_stylesheet'
    _handler = staticfiles.NodeCSSInstance


class TestUserImgInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = staticfiles.UserImgInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post(self.dummyReceiverUser_1['id'])

        img = yield staticfiles.get_model_img(models.User, self.dummyReceiverUser_1['id'])
        self.assertNotEqual(img, '')

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete(self.dummyReceiverUser_1['id'])

        img = yield staticfiles.get_model_img(models.User, self.dummyReceiverUser_1['id'])
        self.assertEqual(img, '')


class TestContextImgInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = staticfiles.ContextImgInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post(self.dummyContext['id'])

        img = yield staticfiles.get_model_img(models.Context, self.dummyContext['id'])
        self.assertNotEqual(img, '')

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete(self.dummyContext['id'])

        img = yield staticfiles.get_model_img(models.Context, self.dummyContext['id'])
        self.assertEqual(img, '')
