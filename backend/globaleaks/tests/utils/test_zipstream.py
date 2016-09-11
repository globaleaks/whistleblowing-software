# -*- encoding: utf-8 -*-

import StringIO
from twisted.internet.defer import inlineCallbacks
from zipfile import ZipFile

from globaleaks.tests import helpers
from globaleaks.utils.zipstream import ZipStream


class TestZipStream(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        self.files = []
        for k in self.internationalized_text:
            self.files.append({'name': self.internationalized_text[k].encode('utf8'),
                               'buf': self.internationalized_text[k].encode('utf-8')})

    def test_zipstream(self):
        output = StringIO.StringIO()

        for data in ZipStream(self.files):
            output.write(data)

        with ZipFile(output, 'r') as f:
            self.assertIsNone(f.testzip())
