import scrypt
import binascii

from twisted.trial import unittest

from globaleaks.security import SALT_LENGTH, set_password, check_password, change_password
from globaleaks.rest.errors import InvalidInputFormat

class TestValidate(unittest.TestCase):

    def test_pass_hash(self):
        dummy_password = r"focaccina"
        dummy_salt = r"vecna@focaccina.net"

        sure_bin = scrypt.hash(dummy_password, dummy_salt[:SALT_LENGTH])
        sure = binascii.b2a_base64(sure_bin)
        not_sure = set_password(dummy_password, dummy_salt)
        self.assertEqual(sure, not_sure)

    def test_valid_password(self):
        dummy_password = dummy_salt = \
            "http://blog.transparency.org/wp-content/uploads/2010/05/A2_Whistelblower_poster.jpg"

        hashed = binascii.b2a_base64(scrypt.hash(dummy_password, dummy_salt[:SALT_LENGTH]))
        self.assertTrue(check_password(dummy_password, hashed, dummy_salt))

    def test_change_password(self):
        dummy_salt = "xxxxxxxx"
        first_pass = "first_password"
        second_pass = "second_password"

        hashed1 = binascii.b2a_base64(scrypt.hash(first_pass, dummy_salt[:SALT_LENGTH]))
        hashed2 = change_password(hashed1, first_pass, second_pass, dummy_salt)

        self.assertEqual(
            hashed2,
            binascii.b2a_base64(scrypt.hash(second_pass, dummy_salt[:SALT_LENGTH]) )
        )

    def test_salt_minlength(self):
        dummy_password = u"latte"
        short_salt = u"x" * (SALT_LENGTH -1)

        try:
            set_password(dummy_password, short_salt)
            self.assertTrue(False)
        except InvalidInputFormat:
            self.assertTrue(True)
