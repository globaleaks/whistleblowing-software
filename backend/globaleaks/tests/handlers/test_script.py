# -*- coding: utf-8 -*-
import os
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import script
from globaleaks.rest.errors import ResourceNotFound
from globaleaks.settings import Settings
from globaleaks.tests import helpers


class TestFileInstance(helpers.TestHandler):
    _handler = script.ScriptHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request()
        x = yield handler.get()

        self.assertEqual(x, "")

        path = os.path.abspath(os.path.join(Settings.scripts_path, '1'))
        with open(path, 'w') as f:
            f.write('script')

        x = yield handler.get()

        self.assertIsNone(x)
