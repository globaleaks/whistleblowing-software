# -*- coding: utf-8 -*-

from globaleaks import models
from globaleaks.handlers.admin import modelimgs
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestModelImgInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = modelimgs.ModelImgInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post('users', self.dummyReceiverUser_1['id'])

        img = yield modelimgs.get_model_img(1, 'users', self.dummyReceiverUser_1['id'])
        self.assertNotEqual(img, '')

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete('users', self.dummyReceiverUser_1['id'])

        img = yield modelimgs.get_model_img(1, 'users', self.dummyReceiverUser_1['id'])
        self.assertEqual(img, '')
