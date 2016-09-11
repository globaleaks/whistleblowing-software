# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import files
from globaleaks.tests import helpers


class TestFileInstance(helpers.TestHandler):
    _handler = files.FileInstance

    @inlineCallbacks
    def test_post(self):
        handler = self.request({}, role='admin')

        yield handler.post(u'antani')

    @inlineCallbacks
    def test_delete(self):
        handler = self.request({}, role='admin')
        yield handler.delete(u'antani')

        img = yield files.get_file(u'antani')
        self.assertEqual(img, '')
