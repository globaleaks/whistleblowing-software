# -*- coding: utf-8
import os

from globaleaks.utils.securetempfile import SecureTemporaryFile
from globaleaks.settings import Settings
from globaleaks.tests import helpers


class TestSecureFiles(helpers.TestGL):
    def test_temporary_file(self):
        a = SecureTemporaryFile(Settings.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        a.close()
        self.assertFalse(os.path.exists(a.filepath))

    def test_temporary_file_write_after_read(self):
        a = SecureTemporaryFile(Settings.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        self.assertRaises(Exception, a.write, antani)
        a.close()
