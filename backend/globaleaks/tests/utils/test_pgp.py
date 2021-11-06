# -*- coding: utf-8
import os
from datetime import datetime

from globaleaks.tests import helpers
from globaleaks.utils.pgp import PGPContext


class TestPGP(helpers.TestGL):
    secret_content = helpers.PGPKEYS['VALID_PGP_KEY1_PRV']

    def test_encrypt_message(self):
        fake_receiver_desc = {
            'pgp_key_public': helpers.PGPKEYS['VALID_PGP_KEY1_PUB'],
            'pgp_key_fingerprint': 'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1',
            'username': 'fake@username.net',
        }

        pgpctx = PGPContext(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])

        encrypted_body = pgpctx.encrypt_message(self.secret_content)

        self.assertEqual(str(pgpctx.gnupg.decrypt(encrypted_body)), self.secret_content)

    def test_encrypt_file(self):
        file_src = os.path.join(os.getcwd(), 'test_plaintext_file.txt')
        file_dst = os.path.join(os.getcwd(), 'test_encrypted_file.txt')

        fake_receiver_desc = {
            'pgp_key_public': helpers.PGPKEYS['VALID_PGP_KEY1_PRV'],
            'pgp_key_fingerprint': 'BFB3C82D1B5F6A94BDAC55C6E70460ABF9A4C8C1',
            'username': 'fake@username.net',
        }

        # these are the same lines used in delivery.py
        pgpctx = PGPContext(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])

        with open(file_src, 'wb+') as f:
            f.write(self.secret_content.encode())
            f.seek(0)

            pgpctx.encrypt_file(f, file_dst)

        with open(file_dst, 'rb') as f:
            self.assertEqual(str(pgpctx.gnupg.decrypt_file(f)), self.secret_content)

    def test_read_expirations(self):
        pgpctx = PGPContext(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])

        self.assertEqual(pgpctx.expiration,
                         datetime.utcfromtimestamp(0))

        pgpctx = PGPContext(helpers.PGPKEYS['EXPIRED_PGP_KEY_PUB'])

        self.assertEqual(pgpctx.expiration,
                         datetime.utcfromtimestamp(1391012793))
