import binascii
import os
import scrypt
from datetime import datetime

from globaleaks.rest import errors
from globaleaks.security import generateRandomSalt, hash_password, check_password, change_password, \
    directory_traversal_check, SecureTemporaryFile, GLBPGP
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.trial import unittest


class TestPasswordManagement(unittest.TestCase):
    def test_pass_hash(self):
        dummy_password = "focaccina"

        dummy_salt = generateRandomSalt()

        sure_bin = scrypt.hash(dummy_password, dummy_salt)
        sure = binascii.b2a_hex(sure_bin)
        not_sure = hash_password(dummy_password, dummy_salt)
        self.assertEqual(sure, not_sure)

    def test_valid_password(self):
        dummy_password = "http://blog.transparency.org/wp-content/uploads/2010/05/A2_Whistelblower_poster.jpg"
        dummy_salt = generateRandomSalt()

        hashed_once = binascii.b2a_hex(scrypt.hash(dummy_password, dummy_salt))
        hashed_twice = binascii.b2a_hex(scrypt.hash(dummy_password, dummy_salt))
        self.assertTrue(hashed_once, hashed_twice)

        self.assertTrue(check_password(dummy_password, dummy_salt, hashed_once))

    def test_change_password(self):
        first_pass = helpers.VALID_PASSWORD1
        second_pass = helpers.VALID_PASSWORD2
        dummy_salt = generateRandomSalt()

        # as first we hash a "first_password" like has to be:
        hashed1 = binascii.b2a_hex(scrypt.hash(str(first_pass), dummy_salt))

        # now emulate the change unsing the globaleaks.security module
        hashed2 = change_password(hashed1, first_pass, second_pass, dummy_salt)

        # verify that second stored pass is the same
        self.assertEqual(
            hashed2,
            binascii.b2a_hex(scrypt.hash(str(second_pass), dummy_salt))
        )

    def test_change_password_fail_with_invalid_old_password(self):
        dummy_salt_input = "xxxxxxxx"
        first_pass = helpers.VALID_PASSWORD1
        second_pass = helpers.VALID_PASSWORD2
        dummy_salt = generateRandomSalt()

        # as first we hash a "first_password" like has to be:
        hashed1 = binascii.b2a_hex(scrypt.hash(str(first_pass), dummy_salt))

        # now emulate the change unsing the globaleaks.security module
        self.assertRaises(errors.InvalidOldPassword, change_password, hashed1, "invalid_old_pass", second_pass,
                          dummy_salt_input)


class TestFilesystemAccess(helpers.TestGL):
    def test_directory_traversal_failure_on_relative_trusted_path_must_fail(self):
        self.assertRaises(Exception, directory_traversal_check, 'invalid/relative/trusted/path', "valid.txt")

    def test_directory_traversal_check_blocked(self):
        self.assertRaises(errors.DirectoryTraversalError, directory_traversal_check, Settings.files_path,
                          "/etc/passwd")

    def test_directory_traversal_check_allowed(self):
        valid_access = os.path.join(Settings.files_path, "valid.txt")
        directory_traversal_check(Settings.files_path, valid_access)


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


class TestPGP(helpers.TestGL):
    secret_content = helpers.PGPKEYS['VALID_PGP_KEY1_PRV']

    def test_encrypt_message(self):
        fake_receiver_desc = {
            'pgp_key_public': helpers.PGPKEYS['VALID_PGP_KEY1_PUB'],
            'pgp_key_fingerprint': u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1',
            'username': u'fake@username.net',
        }

        pgpobj = GLBPGP()
        pgpobj.load_key(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])

        encrypted_body = pgpobj.encrypt_message(fake_receiver_desc['pgp_key_fingerprint'],
                                                self.secret_content)

        self.assertEqual(str(pgpobj.gnupg.decrypt(encrypted_body)), self.secret_content)

        pgpobj.destroy_environment()

    def test_encrypt_file(self):
        file_src = os.path.join(os.getcwd(), 'test_plaintext_file.txt')
        file_dst = os.path.join(os.getcwd(), 'test_encrypted_file.txt')

        fake_receiver_desc = {
            'pgp_key_public': helpers.PGPKEYS['VALID_PGP_KEY1_PRV'],
            'pgp_key_fingerprint': u'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1',
            'username': u'fake@username.net',
        }

        # these are the same lines used in delivery.py
        pgpobj = GLBPGP()
        pgpobj.load_key(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])

        with open(file_src, 'w+') as f:
            f.write(self.secret_content)
            f.seek(0)

            pgpobj.encrypt_file(fake_receiver_desc['pgp_key_fingerprint'], f, file_dst)

        with open(file_dst, 'r') as f:
            self.assertEqual(str(pgpobj.gnupg.decrypt_file(f)), self.secret_content)

        pgpobj.destroy_environment()

    def test_read_expirations(self):
        pgpobj = GLBPGP()

        self.assertEqual(pgpobj.load_key(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])['expiration'],
                         datetime.utcfromtimestamp(0))

        self.assertEqual(pgpobj.load_key(helpers.PGPKEYS['EXPIRED_PGP_KEY_PUB'])['expiration'],
                         datetime.utcfromtimestamp(1391012793))

        pgpobj.destroy_environment()
