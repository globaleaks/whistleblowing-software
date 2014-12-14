import binascii

import os
import scrypt

from cryptography.hazmat.primitives import hashes
from twisted.trial import unittest

from globaleaks.tests import helpers
from globaleaks.security import get_salt, hash_password, check_password, change_password, check_password_format, SALT_LENGTH, \
                                directory_traversal_check, GLSecureTemporaryFile, GLSecureFile, crypto_backend

from globaleaks.settings import GLSetting
from globaleaks.rest import errors


class TestPasswordManagement(unittest.TestCase):

    def test_pass_hash(self):
        dummy_password = "focaccina"
        dummy_salt_input = "vecna@focaccina.net"

        sure_bin = scrypt.hash(dummy_password, get_salt(dummy_salt_input) )
        sure = binascii.b2a_hex(sure_bin)
        not_sure = hash_password(dummy_password, dummy_salt_input)
        self.assertEqual(sure, not_sure)

    def test_salt(self):
        dummy_string = "xxxxxx32312xxxxxx"

        sha = hashes.Hash(hashes.SHA512(), backend=crypto_backend)
        sha.update(dummy_string)

        complete_hex = digest = binascii.b2a_hex(sha.finalize())
        self.assertEqual( complete_hex[:SALT_LENGTH],
                          get_salt(dummy_string)[:SALT_LENGTH] )

        new_dummy_string = "xxxxkkkk"

        sha_second = hashes.Hash(hashes.SHA512(), backend=crypto_backend)
        sha_second.update(new_dummy_string)

        complete_hex = binascii.b2a_hex(sha_second.finalize())
        self.assertEqual( complete_hex[:SALT_LENGTH],
                          get_salt(new_dummy_string)[:SALT_LENGTH] )

    def test_valid_password(self):
        dummy_password = dummy_salt_input = \
            "http://blog.transparency.org/wp-content/uploads/2010/05/A2_Whistelblower_poster.jpg"
        dummy_salt = get_salt(dummy_salt_input)

        hashed_once = binascii.b2a_hex(scrypt.hash(dummy_password, dummy_salt))
        hashed_twice = binascii.b2a_hex(scrypt.hash(dummy_password, dummy_salt))
        self.assertTrue(hashed_once, hashed_twice)

        self.assertTrue(check_password(dummy_password, hashed_once, dummy_salt_input))

    def test_change_password(self):
        dummy_salt_input = "xxxxxxxx"
        first_pass = helpers.VALID_PASSWORD1
        second_pass = helpers.VALID_PASSWORD2
        dummy_salt = get_salt(dummy_salt_input)

        # as first we hash a "first_password" like has to be:
        hashed1 = binascii.b2a_hex(scrypt.hash(str(first_pass), dummy_salt))

        # now emulate the change unsing the globaleaks.security module
        hashed2 = change_password(hashed1, first_pass, second_pass, dummy_salt_input)

        # verify that second stored pass is the same
        self.assertEqual(
            hashed2,
            binascii.b2a_hex(scrypt.hash(str(second_pass), dummy_salt) )
        )

    def test_pass_hash_with_0_len_pass_must_fail(self):
        dummy_password = ""
        dummy_salt_input = "vecna@focaccina.net"

        sure_bin = scrypt.hash(dummy_password, get_salt(dummy_salt_input) )
        self.assertRaises(errors.InvalidInputFormat, hash_password, dummy_password, dummy_salt_input)

    def test_change_password(self):
        dummy_salt_input = "xxxxxxxx"
        first_pass = helpers.VALID_PASSWORD1
        second_pass = helpers.VALID_PASSWORD2
        dummy_salt = get_salt(dummy_salt_input)

        # as first we hash a "first_password" like has to be:
        hashed1 = binascii.b2a_hex(scrypt.hash(str(first_pass), dummy_salt))

        # now emulate the change unsing the globaleaks.security module
        self.assertRaises(errors.InvalidOldPassword, change_password, hashed1, "invalid_old_pass", second_pass, dummy_salt_input)

    def test_check_password_format(self):
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "123abc") # less than 8 chars
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "withnonumbers") # withnonumbers
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "12345678") #onlynumbers
        check_password_format("abcde12345")

class TestFilesystemAccess(helpers.TestGL):

    def test_directory_traversal_failure_on_relative_trusted_path_must_fail(self):
        self.assertRaises(Exception, directory_traversal_check, 'invalid/relative/trusted/path', "valid.txt")

    def test_directory_traversal_check_blocked(self):
        self.assertRaises(errors.DirectoryTraversalError, directory_traversal_check,GLSetting.static_path, "/etc/passwd")

    def test_directory_traversal_check_allowed(self):
        valid_access = os.path.join(GLSetting.static_path, "valid.txt")
        directory_traversal_check(GLSetting.static_path, valid_access)

class TestGLSecureFiles(helpers.TestGL):

    def test_temporary_file(self):
        a = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        a.close()
        self.assertFalse(os.path.exists(a.filepath))

    def test_temporary_file_write_after_read(self):
        a = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        self.assertRaises(AssertionError, a.write, antani)

    def test_temporary_file_avoid_delete(self):
        a = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        a.avoid_delete()
        antani = "0123456789" * 10000
        a.write(antani)
        a.close()
        self.assertTrue(os.path.exists(a.filepath))
        b = GLSecureFile(a.filepath)
        self.assertTrue(antani == b.read())

    def test_temporary_file_lost_key_due_to_eventual_bug_or_reboot(self):
        a = GLSecureTemporaryFile(GLSetting.tmp_upload_path)
        a.avoid_delete()
        antani = "0123456789" * 10000
        a.write(antani)
        a.close()
        self.assertTrue(os.path.exists(a.filepath))
        os.remove(a.keypath)
        self.assertRaises(IOError, GLSecureFile, a.filepath)
