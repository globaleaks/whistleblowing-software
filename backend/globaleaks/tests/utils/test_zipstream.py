# -*- coding: utf-8 -*-
from io import BytesIO

import os
from six import unichr, binary_type

from twisted.internet.defer import inlineCallbacks
from zipfile import ZipFile

from globaleaks.tests import helpers
from globaleaks.utils.zipstream import ZipStream


class TestZipStream(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        self.unicode_seq = ''.join(unichr(x) for x in range(0x400, 0x40A))

        self.files = [
          {'name': __file__, 'fo': open(os.path.abspath(__file__), 'rb')},
          {'name': __file__, 'path': os.path.abspath(__file__)},
          {'name': self.unicode_seq, 'fo': BytesIO(self.unicode_seq.encode('utf-8'))}
        ]

    def test_zipstream(self):
        output = BytesIO()

        for data in ZipStream(self.files):
            output.write(data)

        with ZipFile(output, 'r') as f:
            self.assertIsNone(f.testzip())

        with ZipFile(output, 'r') as f:
            infolist = f.infolist()
            self.assertTrue(len(infolist), 2)
            for ff in infolist:
                if ff.filename == self.unicode_seq:
                    self.assertTrue(ff.file_size == len(self.unicode_seq.encode()))
                else:
                    self.assertTrue(ff.file_size == os.stat(os.path.abspath(__file__)).st_size)
