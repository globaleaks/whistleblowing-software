# -*- encoding: utf-8 -*-

import os
from zipfile import ZipFile

from twisted.internet.defer import inlineCallbacks

from globaleaks.db.appdata import load_appdata
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers
from globaleaks.utils.zipstream import ZipStream

class TestZipStream(helpers.TestGL):
    files = []

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        for k in self.internationalized_text:
            self.files.append({'name': self.internationalized_text[k].encode('utf8'), 'buf': self.internationalized_text[k].encode('utf-8')})


    def test_zipstream(self):
        current_file = os.path.realpath(__file__)
        with open(current_file, 'w') as f:
            for data in ZipStream(self.files):
                f.write(data)

        with ZipFile(current_file, 'r') as f:
            self.assertIsNone(f.testzip())
