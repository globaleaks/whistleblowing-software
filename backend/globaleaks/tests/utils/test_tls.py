import os
from twisted.trial.unittest import TestCase

from globaleaks.tests import helpers
from globaleaks.utils import tls


class TestKeyGen(TestCase):
    def test_dh_params(self):
        pass


def get_valid_setup():
    test_data_dir = os.path.join(helpers.DATA_DIR, 'https')

    valid_setup_files = {
        'key': 'priv_key.pem',
        'cert': 'cert.pem',
        'chain': 'chain.pem',
        'dh_params': 'dh_params.pem'
    }

    return {
        k : open(os.path.join(test_data_dir, 'valid', fname), 'r').read() \
            for k, fname in valid_setup_files.iteritems()
    }


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
            'rsa_key_monalisa_pass.pem',
            # X.509 cert for the wrong project
            'wonka_cert.pem',
            # Broken X.509 cert
            # 'broken_cert.pem',
            # Expired X.509 cert
            ##'expired_cert.pem',
            # X.509 chain for the wrong project
            # 'nskelsey_dev_chain.pem',
            # X.509 with a broken intermediate
            # 'broken_chain.pem',
        ]

        self.valid_setup = get_valid_setup()

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
        pkv = tls.PrivKeyValidator()

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                self.db_cfg['key'] = f.read()
            ok, err = pkv.validate(self.db_cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_private_key_valid(self):
        pkv = tls.PrivKeyValidator()

        good_keys = [
            'rsa_key.pem',
            'dh_key.pem',
        ]

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']

        for fname in good_keys:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p, 'r') as f:
                self.db_cfg['key'] = f.read()
            ok, err = pkv.validate(self.db_cfg)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_cert_invalid(self):
        crtv = tls.CertValidator()

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.db_cfg['key'] = self.valid_setup['key']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                self.db_cfg['cert'] = f.read()
            ok, err = crtv.validate(self.db_cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_cert_valid(self):
        crtv = tls.CertValidator()

        good_certs = [
            'self_signed_cert.pem',
            'int_signed_cert.pem',
        ]

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.db_cfg['key'] = self.valid_setup['key']

        for fname in good_certs:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p, 'r') as f:
                self.db_cfg['cert'] = f.read()
            ok, err = crtv.validate(self.db_cfg)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_chain_invalid(self):
        chn_v = tls.ChainValidator()

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.db_cfg['key'] = self.valid_setup['key']
        self.db_cfg['cert'] = self.valid_setup['cert']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                print 'testing:',fname
                self.db_cfg['ssl_intermediate'] = f.read()
            ok, err = chn_v.validate(self.db_cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_chain_valid(self):
        chn_v = tls.ChainValidator()

        self.db_cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.db_cfg['key'] = self.valid_setup['key']
        self.db_cfg['cert'] = self.valid_setup['cert']

        p = os.path.join(self.test_data_dir, 'valid', 'ca-all.crt')
        with open(p, 'r') as f:
            self.db_cfg['ssl_intermediate'] = f.read()

        ok, err = chn_v.validate(self.db_cfg)

        self.assertTrue(ok)
        self.assertIsNone(err)
