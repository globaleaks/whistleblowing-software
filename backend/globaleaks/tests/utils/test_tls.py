# -*- coding: utf-8 -*-
import os

from OpenSSL import crypto
from OpenSSL.crypto import FILETYPE_PEM
from twisted.trial.unittest import TestCase

from globaleaks.models.config import PrivateFactory, NodeFactory
from globaleaks.orm import transact
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

    d = {'hostname': 'localhost:9999'}
    for k, fname in valid_setup_files.items():
        with open(os.path.join(test_data_dir, 'valid', fname), 'r') as fd:
            d[k] = unicode(fd.read())

    return d

@transact
def commit_valid_config(store):
    cfg = get_valid_setup()

    priv_fact = PrivateFactory(store, 1)
    priv_fact.set_val(u'https_dh_params', cfg['dh_params'])
    priv_fact.set_val(u'https_priv_key', cfg['key'])
    priv_fact.set_val(u'https_cert', cfg['cert'])
    priv_fact.set_val(u'https_chain', cfg['chain'])
    priv_fact.set_val(u'https_enabled', True)

    NodeFactory(store).set_val(1, u'hostname', 'localhost:9999')


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
            # A cert and chain for the key that are mistakenly combinded
            'cert_and_chain.pem',
            # A certficate repeated a few times
            'duplicated_chain.pem',
        ]

        self.valid_setup = get_valid_setup()

    def setUp(self):
        self.cfg = {
            'key': '',
            'cert': '',
            'chain': '',
            'dh_params': '',
            'ssl_intermediate': '',
            'https_enabled': False,
            'hostname': 'localhost:9999',
        }

    def test_private_key_invalid(self):
        pkv = tls.PrivKeyValidator()

        self.cfg['ssl_dh'] = self.valid_setup['dh_params']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                self.cfg['ssl_key'] = f.read()
            ok, err = pkv.validate(self.cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_private_key_valid(self):
        pkv = tls.PrivKeyValidator()

        good_keys = [
            'priv_key.pem'
        ]

        self.cfg['ssl_dh'] = self.valid_setup['dh_params']

        for fname in good_keys:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p, 'r') as f:
                self.cfg['ssl_key'] = f.read()
            ok, err = pkv.validate(self.cfg)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_cert_invalid(self):
        crtv = tls.CertValidator()

        self.cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.cfg['ssl_key'] = self.valid_setup['key']

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                self.cfg['ssl_cert'] = f.read()
            ok, err = crtv.validate(self.cfg)
            self.assertFalse(ok)
            self.assertIsNotNone(err)

    def test_cert_valid(self):
        crtv = tls.CertValidator()

        good_certs = [
            'cert.pem'
        ]

        self.cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.cfg['ssl_key'] = self.valid_setup['key']

        for fname in good_certs:
            p = os.path.join(self.test_data_dir, 'valid', fname)
            with open(p, 'r') as f:
                self.cfg['ssl_cert'] = f.read()
            ok, err = crtv.validate(self.cfg)
            self.assertTrue(ok)
            self.assertIsNone(err)

    def test_chain_invalid(self):
        chn_v = tls.ChainValidator()

        self.cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.cfg['ssl_key'] = self.valid_setup['key']
        self.cfg['ssl_cert'] = self.valid_setup['cert']

        exceptions_from_validation = {'empty.txt'}

        for fname in self.invalid_files:
            p = os.path.join(self.test_data_dir, 'invalid', fname)
            with open(p, 'r') as f:
                self.cfg['ssl_intermediate'] = f.read()

            ok, err = chn_v.validate(self.cfg)
            if not fname in exceptions_from_validation:
                self.assertFalse(ok)
                self.assertIsNotNone(err)
            else:
                self.assertTrue(ok)
                self.assertIsNone(err)

    def test_chain_valid(self):
        chn_v = tls.ChainValidator()

        self.cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.cfg['ssl_key'] = self.valid_setup['key']
        self.cfg['ssl_cert'] = self.valid_setup['cert']

        p = os.path.join(self.test_data_dir, 'valid', 'chain.pem')
        with open(p, 'r') as f:
            self.cfg['ssl_intermediate'] = f.read()

        ok, err = chn_v.validate(self.cfg)
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_check_expiration(self):
        chn_v = tls.ChainValidator()

        self.cfg['ssl_dh'] = self.valid_setup['dh_params']
        self.cfg['ssl_key'] = self.valid_setup['key']

        p = os.path.join(self.test_data_dir, 'invalid/expired_cert_with_valid_prv.pem')
        with open(p, 'r') as f:
            self.cfg['ssl_cert'] = f.read()

        ok, err = chn_v.validate(self.cfg)
        self.assertFalse(ok)
        self.assertTrue(isinstance(err, tls.ValidationException))

        ok, err = chn_v.validate(self.cfg, check_expiration=False)

        self.assertTrue(ok)
        self.assertIsNone(None)

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
            ('invalid/cert_and_chain.pem', 2),
            ('invalid/duplicated_chain.pem', 4),
            ('valid/chains/comodo_chain.pem', 3),
        ]

        for chain_path, chain_len in test_cases:
            p = os.path.join(self.test_data_dir, chain_path)
            with open(p, 'r') as f:
                chain = tls.split_pem_chain(f.read())

            self.assertEqual(len(chain), chain_len)

            # Check one time that the parse produced real results
            if chain_path == 'invalid/cert_and_chain.pem':
                self.assertEqual(self.valid_setup['cert'], chain[0])
                self.assertEqual(self.valid_setup['chain'], chain[1])
