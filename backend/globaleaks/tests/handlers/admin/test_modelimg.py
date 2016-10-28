# -*- coding: utf-8 -*-
from io import BytesIO as StringIO

from twisted.internet.defer import inlineCallbacks
import os
from globaleaks import models
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.handlers.admin import modelimgs
from globaleaks.settings import GLSettings


class TestModelImgInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = modelimgs.ModelImgInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post('users', self.dummyReceiverUser_1['id'])

        img = yield modelimgs.get_model_img(models.User, self.dummyReceiverUser_1['id'])
        self.assertNotEqual(img, '')

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete('users', self.dummyReceiverUser_1['id'])

        img = yield modelimgs.get_model_img(models.User, self.dummyReceiverUser_1['id'])
        self.assertEqual(img, '')
