# -*- coding: utf-8
import os

from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from globaleaks.utils.fs import directory_traversal_check


class TestFilesystemAccess(helpers.TestGL):
    def test_directory_traversal_failure_on_relative_trusted_path_must_fail(self):
        self.assertRaises(Exception, directory_traversal_check, 'invalid/relative/trusted/path', "valid.txt")

    def test_directory_traversal_check_blocked(self):
        self.assertRaises(errors.DirectoryTraversalError, directory_traversal_check, Settings.files_path,
                          "/etc/passwd")

    def test_directory_traversal_check_allowed(self):
        valid_access = os.path.join(Settings.files_path, "valid.txt")
        directory_traversal_check(Settings.files_path, valid_access)
