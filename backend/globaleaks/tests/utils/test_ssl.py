import os
from twisted.trial.unittest import TestCase

from globaleaks.tests import helpers
from globaleaks.utils import ssl

class TestKeyGen(TestCase):
    def test_dh_params(self):
        pass

class TestObjectValidators(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.test_data_dir = os.path.join(helpers.DATA_DIR, 'https')

        self.invalid_files = [
            'empty.txt',
            # Invalid pem string
            'noise.pem',
            # Raw bytes
            'bytes.out',
            # Mangled ASN.1 RSA key
            'garbage_key.pem',
            # DER formatted key
            'rsa_key.der',
            # PKCS8 encrypted private key
            'rsa_key_monalisa_pass.pem',
            # X.509 cert for the wrong project

            # Expired X.509 cert

            # Broken X.509 cert
        ]

        self.valid_setup_files = {
            'key': 'rsa_key.pem',
            'cert': 'cert.pem',
            'chain': 'moon_village_chain.pem',
            'dh_params': 'dh_params.pem'
        }

        self.valid_setup = { 
            k : open(os.path.join(self.test_data_dir, 'valid', fname), 'r').read() \
                for k, fname in self.valid_setup_files.iteritems()
        }


    def setUp(self):
        self.db_cfg = {
            'key': '',
            'cert': '',
            'chain': '',
            'dh_params': '',
            'ssl_intermediate': '',
            'https_enabled': False,
        }



    def test_private_key_invalid(self):
        pkv = ssl.PrivKeyValidator()

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                self.db_cfg['key'] = f.read()
            ok, err = pkv.validate(self.db_cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_private_key_valid(self):
        good_keys = [
            'rsa_key.pem',
            'dh_key.pem',
        ]

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']

        pkv = ssl.PrivKeyValidator()
        for fname in good_keys:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p, 'r') as f:
                self.db_cfg['key'] = f.read()
            ok, err = pkv.validate(self.db_cfg)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_cert_invalid(self):
        pkv = ssl.CertValidator()
        
        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.db_cfg['key'] = self.valid_setup['key']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                self.db_cfg['cert'] = f.read()
            ok, err = pkv.validate(self.db_cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_cert_valid(self):
        pass

    def test_chain_invalid(self):
        pass

    def test_chain_valid(self):
        pass
