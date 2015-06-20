# -*- encoding: utf-8 -*-

import os
from zipfile import ZipFile

from twisted.internet.defer import inlineCallbacks

from globaleaks.db.datainit import load_appdata
from globaleaks.settings import GLSetting
from globaleaks.tests import helpers
from globaleaks.utils.zipstream import ZipStream, get_compression_opts

class TestCollection(helpers.TestGL):
    files = []

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)
        self.test_collection_file = os.path.join(GLSetting.working_path, 'test.collection')

        for k in self.internationalized_text:
            self.files.append({'name': self.internationalized_text[k].encode('utf8'), 'buf': self.internationalized_text[k].encode('utf-8')})


    def test_collection(self):
        for compression in ['zipstored', 'zipdeflated']:
            with open(self.test_collection_file, 'w') as f:
                opts = get_compression_opts(compression)
                for data in ZipStream(self.files, opts['compression_type']):
                    f.write(data)

            with ZipFile(self.test_collection_file, 'r') as f:
                self.assertIsNone(f.testzip())
