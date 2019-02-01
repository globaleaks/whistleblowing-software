# -*- coding: utf-8
import filecmp
import os

from globaleaks.settings import Settings
from globaleaks.tests import helpers
from globaleaks.utils.crypto import GCE

password = b'password'
message = b'message'
salt = GCE.generate_salt()


class TestCryptoUtils(helpers.TestGL):
    def test_generate_key(self):
        GCE.generate_key()

    def test_generate_keypair(self):
        key = GCE.generate_key()
        prv_key, pub_key = GCE.generate_keypair()
        prv_key_enc = GCE.symmetric_encrypt(key, prv_key)
        self.assertEqual(prv_key, GCE.symmetric_decrypt(key, prv_key_enc))

    def test_export_import_key(self):
        x1, _ = GCE.generate_keypair()
        x2 = GCE.export_private_key(x1)
        x3 = GCE.import_private_key(x2)
        self.assertEqual(x1, x3._private_key)

    def test_derive_key(self):
        GCE.derive_key(password, salt)

    def test_crypto_generate_key_encrypt_decrypt_key(self):
        enc_key = GCE.generate_key()
        enc = GCE.symmetric_encrypt(enc_key, message)
        dec = GCE.symmetric_decrypt(enc_key, enc)
        self.assertEqual(dec, message)

    def test_crypto_generate_encrypt_decrypt_message(self):
        prv_key, pub_key = GCE.generate_keypair()
        enc = GCE.asymmetric_encrypt(pub_key, message)
        dec = GCE.asymmetric_decrypt(prv_key, enc)
        self.assertEqual(dec, message)

    def test_check_password(self):
        hash = GCE.hash_password(password, salt)
        self.assertTrue(GCE.check_password(GCE.HASH, password, salt, hash))
        self.assertFalse(GCE.check_password(GCE.HASH, password, salt, 'nohashnoparty'))

    def test_encrypt_and_decrypt_file(self):
        chunk_size = 1
        prv_key, pub_key = GCE.generate_keypair()
        a = __file__
        b = os.path.join(Settings.tmp_path, 'b')
        c = os.path.join(Settings.tmp_path, 'c')

        with open(a, 'rb') as input_fd, GCE.streaming_encryption_open('ENCRYPT', pub_key, b) as seo:
            chunk = input_fd.read(1)
            while(True):
                x = input_fd.read(1)
                if not x:
                    seo.encrypt_chunk(chunk, 1)
                    break

                seo.encrypt_chunk(chunk, 0)

                chunk = x

        with open(c, 'wb') as output_fd,\
             GCE.streaming_encryption_open('DECRYPT', prv_key, b) as seo:

            while(True):
                last, data = seo.decrypt_chunk()
                output_fd.write(data)
                if last:
                    break

        self.assertFalse(filecmp.cmp(a, b, False))
        self.assertTrue(filecmp.cmp(a, c, False))
