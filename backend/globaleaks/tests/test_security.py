import binascii
from cryptography.hazmat.primitives import hashes
from datetime import datetime
import os
import scrypt

from twisted.trial import unittest
from globaleaks.tests import helpers
from globaleaks.security import generateRandomSalt, hash_password, check_password, change_password, \
    check_password_format, directory_traversal_check, GLSecureTemporaryFile, GLSecureFile, \
    crypto_backend, GLBPGP
from globaleaks.settings import GLSettings
from globaleaks.rest import errors


class TestPasswordManagement(unittest.TestCase):
    def test_pass_hash(self):
        dummy_password = "focaccina"

        dummy_salt = generateRandomSalt()

        sure_bin = scrypt.hash(dummy_password, dummy_salt)
        sure = binascii.b2a_hex(sure_bin)
        not_sure = hash_password(dummy_password, dummy_salt)
        self.assertEqual(sure, not_sure)

    def test_valid_password(self):
        dummy_password = dummy_salt_input = \
            "http://blog.transparency.org/wp-content/uploads/2010/05/A2_Whistelblower_poster.jpg"
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

    def test_check_password_format(self):
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "123abc")  # less than 8 chars
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "withnonumbers")  # withnonumbers
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "12345678")  # onlynumbers
        check_password_format("abcde12345")


class TestFilesystemAccess(helpers.TestGL):
    def test_directory_traversal_failure_on_relative_trusted_path_must_fail(self):
        self.assertRaises(Exception, directory_traversal_check, 'invalid/relative/trusted/path', "valid.txt")

    def test_directory_traversal_check_blocked(self):
        self.assertRaises(errors.DirectoryTraversalError, directory_traversal_check, GLSettings.static_path,
                          "/etc/passwd")

    def test_directory_traversal_check_allowed(self):
        valid_access = os.path.join(GLSettings.static_path, "valid.txt")
        directory_traversal_check(GLSettings.static_path, valid_access)


class TestGLSecureFiles(helpers.TestGL):
    def test_temporary_file(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        a.close()
        self.assertFalse(os.path.exists(a.filepath))

    def test_temporary_file_write_after_read(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        self.assertRaises(AssertionError, a.write, antani)
        a.close()

    def test_temporary_file_avoid_delete(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        a.avoid_delete()
        antani = "0123456789" * 10000
        a.write(antani)
        a.close()
        self.assertTrue(os.path.exists(a.filepath))
        b = GLSecureFile(a.filepath)
        self.assertTrue(antani == b.read())
        b.close()

    def test_temporary_file_lost_key_due_to_eventual_bug_or_reboot(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        a.avoid_delete()
        antani = "0123456789" * 10000
        a.write(antani)
        a.close()
        self.assertTrue(os.path.exists(a.filepath))
        os.remove(a.keypath)
        self.assertRaises(IOError, GLSecureFile, a.filepath)
        a.close()

PGPROOT = os.path.join(os.getcwd(), "testing_dir", "gnupg")


class TestPGP(helpers.TestGL):
    def test_encrypt_message(self):
        mail_content = "https://www.youtube.com/watch?v=FYdX0W96-os"

        GLSettings.pgproot = PGPROOT

        fake_receiver_desc = {
            'pgp_key_public': unicode(helpers.VALID_PGP_KEY1),
            'pgp_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
            'pgp_key_status': u'enabled',
            'username': u'fake@username.net',
        }

        pgpobj = GLBPGP()
        pgpobj.load_key(helpers.VALID_PGP_KEY1)

        encrypted_body = pgpobj.encrypt_message(fake_receiver_desc['pgp_key_fingerprint'], mail_content)
        self.assertSubstring('-----BEGIN PGP MESSAGE-----', encrypted_body)
        self.assertSubstring('-----END PGP MESSAGE-----', encrypted_body)

        pgpobj.destroy_environment()

    def test_encrypt_file(self):
        # setup the PGP key before
        GLSettings.pgproot = PGPROOT

        tempsource = os.path.join(os.getcwd(), "temp_source.txt")
        with file(tempsource, 'w+') as f1:
            f1.write("\n\nDecrypt the Cat!\n\nhttp://tobtu.com/decryptocat.php\n\n")

            f1.seek(0)

            fake_receiver_desc = {
                'pgp_key_public': unicode(helpers.VALID_PGP_KEY1),
                'pgp_key_status': u'enabled',
                'pgp_key_fingerprint': u"CF4A22020873A76D1DCB68D32B25551568E49345",
                'username': u'fake@username.net',
            }

            # these are the same lines used in delivery_sched.py
            pgpobj = GLBPGP()
            pgpobj.load_key(helpers.VALID_PGP_KEY1)
            encrypted_file_path, encrypted_file_size = pgpobj.encrypt_file(fake_receiver_desc['pgp_key_fingerprint'],
                                                                           tempsource, f1, "/tmp")
            pgpobj.destroy_environment()

            with file(encrypted_file_path, "r") as f2:
                first_line = f2.readline()

            self.assertSubstring('-----BEGIN PGP MESSAGE-----', first_line)

            with file(encrypted_file_path, "r") as f2:
                whole = f2.read()

            self.assertEqual(encrypted_file_size, len(whole))

    def test_pgp_read_expirations(self):
        pgpobj = GLBPGP()

        self.assertEqual(pgpobj.load_key(helpers.VALID_PGP_KEY1)['expiration'],
                         datetime.utcfromtimestamp(0))

        self.assertEqual(pgpobj.load_key(helpers.EXPIRED_PGP_KEY)['expiration'],
                         datetime.utcfromtimestamp(1391012793))

        pgpobj.destroy_environment()
