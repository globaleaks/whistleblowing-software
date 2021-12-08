# -*- coding: utf-8
import os

from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from globaleaks.utils import fs


class TestFilesystemUtilities(helpers.TestGL):
    def test_directory_traversal_failure_on_relative_trusted_path_must_fail(self):
        self.assertRaises(Exception, fs.directory_traversal_check, 'invalid/relative/trusted/path', "valid.txt")

    def test_directory_traversal_check_blocked(self):
        self.assertRaises(errors.DirectoryTraversalError, fs.directory_traversal_check, Settings.files_path,
                          "/etc/passwd")

    def test_directory_traversal_check_allowed(self):
        valid_access = os.path.join(Settings.files_path, "valid.txt")
        fs.directory_traversal_check(Settings.files_path, valid_access)

    def test_srm(self):
        path = os.path.join(Settings.working_path, "antani.txt")

        f = open(path, "wb")
        f.seek((10 * 1024 * 1024) - 1)
        f.write(b"\0")
        f.close()

        self.assertTrue(os.path.isfile(path))

        fs.srm(path, 10)

        self.assertFalse(os.path.isfile(path))
