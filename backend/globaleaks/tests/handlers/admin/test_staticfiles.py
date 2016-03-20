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

crappyjunk = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def get_dummy_file():
    dummyfile = StringIO()
    dummyfile.write(crappyjunk)

    return {
      'body': dummyfile,
      'body_len': len(crappyjunk),
      'content_type': 'image/png',
      'filename': 'img.png'
    }

@transact_ro
def get_node_img_id(store):
    return store.find(models.Node).one().logo_id

@transact_ro
def get_user_img_id(store, obj_id):
    return store.find(models.User, models.User.id == obj_id).one().img_id

@transact_ro
def get_context_img_id(store, obj_id):
    return store.find(models.Context, models.Context.id == obj_id).one().img_id


class TestStaticFileInstance(helpers.TestHandler):
    _handler = staticfiles.StaticFileInstance
    fakeFile = get_dummy_file()

    @inlineCallbacks
    def test_post(self):
        request_body = self.get_dummy_file(filename='img.png', content_type='image/png')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post(filename='img.png')

    @inlineCallbacks
    def test_delete_on_existent_file(self):
        realpath = os.path.join(GLSettings.static_path, self.fakeFile['filename'])
        dumped_file = yield staticfiles.dump_static_file(self.fakeFile, realpath)
        self.assertTrue('filelocation' in dumped_file)

        handler = self.request({}, role='admin')
        yield handler.delete("img.png")

    def test_delete_non_existent_file(self):
        handler = self.request({}, role='admin')
        self.assertRaises(errors.StaticFileNotFound, handler.delete, filename='not_existent.txt')


class TestStaticFileList(helpers.TestHandler):
    _handler = staticfiles.StaticFileList
    fakeFile = get_dummy_file()

    @inlineCallbacks
    def test_get_list_of_files(self):
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
                self.assertEqual(self.fakeFile['body_len'], f['size'])

        self.assertTrue(found)


class TestNodeLogoInstance(helpers.TestHandler):
    _handler = staticfiles.NodeLogoInstance

    @inlineCallbacks
    def test_post(self):
        request_body = self.get_dummy_file(filename='img.png', content_type='image/png')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post()

        img_id = yield get_node_img_id()
        self.assertIsNotNone(img_id)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete()

        img_id = yield get_node_img_id()
        self.assertIsNone(img_id)


class TestUserImgInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = staticfiles.UserImgInstance

    @inlineCallbacks
    def test_post(self):
        request_body = self.get_dummy_file(filename='img.png', content_type='image/png')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post(self.dummyReceiverUser_1['id'])

        img_id = yield get_user_img_id(self.dummyReceiverUser_1['id'])
        self.assertIsNotNone(img_id)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete(self.dummyReceiverUser_1['id'])

        img_id = yield get_user_img_id(self.dummyReceiverUser_1['id'])
        self.assertIsNone(img_id)


class TestContextImgInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = staticfiles.ContextImgInstance

    @inlineCallbacks
    def test_post(self):
        request_body = self.get_dummy_file(filename='img.png', content_type='image/png')

        handler = self.request({}, role='admin', body=request_body)

        yield handler.post(self.dummyContext['id'])

        img_id = yield get_context_img_id(self.dummyContext['id'])
        self.assertIsNotNone(img_id)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete(self.dummyContext['id'])

        img_id = yield get_context_img_id(self.dummyContext['id'])
        self.assertIsNone(img_id)
