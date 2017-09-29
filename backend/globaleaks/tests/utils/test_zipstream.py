# -*- coding: utf-8 -*-
import StringIO
import os
from zipfile import ZipFile

from globaleaks.tests import helpers
from globaleaks.utils.zipstream import ZipStream
from twisted.internet.defer import inlineCallbacks


class TestZipStream(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        self.unicode_seq = ''.join(unichr(x) for x in range(0x400, 0x40A))

        self.files = [
          {'name': self.unicode_seq, 'buf': self.unicode_seq},
          {'name': __file__, 'path': os.path.abspath(__file__)}
        ]

    def test_zipstream(self):
        output = StringIO.StringIO()

        for data in ZipStream(self.files):
            output.write(data)

        with ZipFile(output, 'r') as f:
            self.assertIsNone(f.testzip())

        with ZipFile(output, 'r') as f:
            infolist = f.infolist()
            self.assertTrue(len(infolist), 2)
            for ff in infolist:
                if ff.filename == self.unicode_seq:
                    self.assertTrue(ff.file_size == len(self.unicode_seq))
                else:
                    self.assertTrue(ff.file_size == os.stat(os.path.abspath(__file__)).st_size)
