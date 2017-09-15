# -*- coding: utf-8 -*-

from globaleaks.handlers.admin import files
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestFileInstance(helpers.TestHandler):
    _handler = files.FileInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post(u'antani')

        img = yield files.get_file(1, u'antani')
        self.assertEqual(img, helpers.VALID_BASE64_IMG)

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete(u'antani')

        img = yield files.get_file(1, u'antani')
        self.assertEqual(img, '')
