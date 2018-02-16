# -*- coding: utf-8 -*-
from globaleaks.handlers import file
from globaleaks.handlers.admin import file as admin_file
from globaleaks.rest import errors
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestFileInstance(helpers.TestHandler):
    _handler = file.FileHandler

    @inlineCallbacks
    def test_post(self):
        handler = self.request()
        yield self.assertFailure(handler.get(u'upload.pdf'), errors.ModelNotFound)

        self._handler = admin_file.FileInstance
        handler = self.request({}, role='admin')
        yield handler.post('custom')

        self._handler = file.FileHandler
        handler = self.request()
        x = yield handler.get(u'upload.pdf')

        self.assertIsNone(x)
