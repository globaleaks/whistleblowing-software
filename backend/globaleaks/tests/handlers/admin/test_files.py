# -*- coding: utf-8 -*-
from io import BytesIO as StringIO

from twisted.internet.defer import inlineCallbacks
import os
from globaleaks import models
from globaleaks.orm import transact_ro
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.handlers.admin import files
from globaleaks.settings import GLSettings


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
