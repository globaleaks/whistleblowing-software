# -*- coding: utf-8 -*-
import os

from OpenSSL import crypto
from OpenSSL.crypto import FILETYPE_PEM
from twisted.trial.unittest import TestCase

from globaleaks.tests import helpers
from globaleaks.utils import tls



class TestObjectValidators(TestCase):
    def __init__(self, *args, **kwargs):
        super(TestObjectValidators, self).__init__(*args, **kwargs)
        self.test_data_dir = os.path.join(helpers.DATA_DIR, 'https')

        self.invalid_files = [
            'empty.txt',
            # Invalid pem string
            'noise.pem',
            # Raw bytes
            'bytes.out',
            # A certificate signing request
            'random_csr.pem',
            # Mangled ASN.1 RSA key
            'garbage_key.pem',
            # DER formatted key
            'rsa_key.der',
            # PKCS8 encrypted private key
            'rsa_key_monalisa_pass.pem'
        ]

    def setUp(self):
        self.cfg = {
            'key': '',
            'cert': '',
            'chain': '',
            'ssl_intermediate': '',
            'https_enabled': False,
            'hostname': '127.0.0.1:9999',
        }

    def test_private_key_invalid(self):
        pkv = tls.KeyValidator()

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'rb') as f:
                self.cfg['ssl_key'] = f.read()
            ok, err = pkv.validate(self.cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_private_key_valid(self):
        pkv = tls.KeyValidator()

        good_keys = [
            'key.pem'
        ]

        for fname in good_keys:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p, 'r') as f:
                self.cfg['ssl_key'] = f.read()
            ok, err = pkv.validate(self.cfg)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_cert_invalid(self):
        crtv = tls.CertValidator()

        self.cfg['ssl_key'] = helpers.HTTPS_DATA['key']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'rb') as f:
                self.cfg['ssl_cert'] = f.read()
            ok, err = crtv.validate(self.cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_cert_valid(self):
        crtv = tls.CertValidator()

        good_certs = [
            'cert.pem'
        ]

        self.cfg['ssl_key'] = helpers.HTTPS_DATA['key']

        for fname in good_certs:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p, 'rb') as f:
                self.cfg['ssl_cert'] = f.read()
            ok, err = crtv.validate(self.cfg)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_duplicated_cert_as_chain(self):
        chn_v = tls.ChainValidator()

        self.cfg['ssl_key'] = helpers.HTTPS_DATA['key'].encode()
        self.cfg['ssl_cert'] = helpers.HTTPS_DATA['cert'].encode()

        self.cfg['ssl_intermediate'] = helpers.HTTPS_DATA['cert'].encode()

        ok, err = chn_v.validate(self.cfg)
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_chain_valid(self):
        chn_v = tls.ChainValidator()

        self.cfg['ssl_key'] = helpers.HTTPS_DATA['key'].encode()
        self.cfg['ssl_cert'] = helpers.HTTPS_DATA['cert'].encode()

        p = os.path.join(self.test_data_dir, 'valid', 'chain.pem')
        with open(p, 'rb') as f:
            self.cfg['ssl_intermediate'] = f.read()

        ok, err = chn_v.validate(self.cfg)
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_check_expiration(self):
        chn_v = tls.ChainValidator()

        self.cfg['ssl_key'] = helpers.HTTPS_DATA['key'].encode()

        p = os.path.join(self.test_data_dir, 'invalid/expired_cert_with_valid_prv.pem')
        with open(p, 'rb') as f:
            self.cfg['ssl_cert'] = f.read()

        ok, err = chn_v.validate(self.cfg, check_expiration=True)
        self.assertFalse(ok)
        self.assertTrue(isinstance(err, tls.ValidationException))

    def test_get_issuer_name(self):
        test_cases = [
            ('invalid/le-staging-chain.pem', 'Fake LE Root X1'),
            ('invalid/glbc_le_stage_cert.pem', 'Fake LE Intermediate X1'),
            ('invalid/expired_cert.pem', 'Zintermediate'),
            ('valid/cert.pem', 'Whistleblowing Solutions I.S. S.r.l.'),
        ]
        for cert_path, issuer_name in test_cases:
            p = os.path.join(self.test_data_dir, cert_path)
            with open(p, 'r') as f:
                x509 = crypto.load_certificate(FILETYPE_PEM, f.read())

            res = tls.parse_issuer_name(x509)

            self.assertEqual(res, issuer_name)

    def test_split_pem_chain(self):
        test_cases = [
            ('invalid/bytes.out', 0),
            ('invalid/garbage_key.pem', 0),
            ('invalid/glbc_le_stage_cert.pem', 1),
            ('invalid/expired_cert.pem', 1),
            ('invalid/le-staging-chain.pem', 1),
            ('valid/chain.pem', 2),
        ]

        for chain_path, chain_len in test_cases:
            p = os.path.join(self.test_data_dir, chain_path)
            with open(p, 'rb') as f:
                chain = tls.split_pem_chain(f.read())

            calced_chain_len = 0
            if chain is not None:
                calced_chain_len = len(chain)

            self.assertEqual(calced_chain_len, chain_len)
