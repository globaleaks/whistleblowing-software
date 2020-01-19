# -*- coding: utf-8 -*-
from globaleaks.handlers.admin import modelimgs
from globaleaks.tests import helpers


class TestModelImgInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = modelimgs.ModelImgInstance

    def test_post(self):
        handler = self.request({}, role='admin')

        return handler.post('users', self.dummyReceiver_1['id'])

    def test_delete(self):
        handler = self.request({}, role='admin')
        return handler.delete('users', self.dummyReceiver_1['id'])
