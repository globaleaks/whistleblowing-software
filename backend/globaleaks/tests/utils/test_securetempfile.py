# -*- coding: utf-8
import os
from six import text_type

from globaleaks.utils.securetempfile import SecureTemporaryFile, SecureTemporaryFile
from globaleaks.settings import Settings
from globaleaks.tests import helpers

class TestSecureTemporaryFiles(helpers.TestGL):
    def test_temporary_file(self):
        a = SecureTemporaryFile(Settings.tmp_path)
        antani = "0123456789"
        with a.open('w') as f:
            for _ in range(1000):
                f.write(antani)
            f.finalize_write()

        with a.open('r') as f:
            for x in range(1000):
                self.assertTrue(antani == text_type(f.read(10), 'utf-8'))
