import os

import twisted
from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, defer
from OpenSSL import crypto, SSL

from globaleaks.handlers.admin import https
from globaleaks.models.config import PrivateFactory
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils import tls

from globaleaks.tests import helpers


class TestCryptoFuncs(TestCase):
    def test_it_all(self):
        key_pair = https.gen_RSA_key()

        d = {
         'CN': 'fakedom.blah.blah',
         'O': 'widgets-R-us',
        }

        csr = https.gen_x509_csr(key_pair, d)
        pem_csr = crypto.dump_certificate_request(SSL.FILETYPE_PEM, csr)


#class TestHTTPSWorkers(TestCase):
#    def test_launch_workers(self):
#        pass
#        d = {
#            'cert': '',
#            #'chain': '',
#            #'dh': '',
#            'priv_key': '',
#        }
#
#        for key in d.keys():
#            with open(os.path.join(helpers.DATA_DIR, 'https', key+'.pem')) as f:
#                d[key] = f.read()
#
#        pool = https.https_master.launch_worker({}, d['priv_key'], d['cert'], '', '')
#
#        d = defer.gatherResults([p.deferredConnect for p in pool])
#        def test_cb(ignored):
#            print('Resolving final defered', ignored)
#
#        d.addCallback(test_cb)
#        return d
#
#        #from twisted.internet import reactor
#        #from IPython import embed; embed()
#        #import time; time.sleep(60)


class TestFileHandler(helpers.TestHandler):
    
    _handler = https.FileHandler

    valid_setup_files = {
        'key': 'rsa_key.pem',
        'cert': 'cert.pem',
        'chain': 'moon_village_chain.pem',
        'dh_params': 'dh_params.pem'
    }

    @inlineCallbacks
    def setUp(self):
        yield super(TestFileHandler, self).setUp()

        self.test_data_dir = os.path.join(helpers.DATA_DIR, 'https')

        self.valid_setup = { 
            k : open(os.path.join(self.test_data_dir, 'valid', fname), 'r').read() \
                for k, fname in self.valid_setup_files.iteritems()
        }

        @transact
        def set_dh_params(store):
            dh_params = self.valid_setup['dh_params']
            PrivateFactory(store).set_val('https_dh_params', dh_params)
        yield set_dh_params()

    @inlineCallbacks
    def is_set(self, name, is_set):
        handler = self.request(role='admin', handler_cls=https.ConfigHandler)

        yield handler.get()
        resp = self.responses[-1]

        self.assertEqual(resp['files'][name]['set'], is_set)

    @transact
    def set_enabled(self, store):
        PrivateFactory(store).set_val('https_enabled', True)

    @inlineCallbacks
    def test_priv_key_file(self):
        n = 'priv_key'

        yield self.is_set(n, False)

        # Try to upload an invalid key
        bad_key = 'donk donk donk donk donk donk'
        handler = self.request({'content': bad_key}, role='admin')
        yield self.assertFailure(handler.post(n), errors.ValidationError)

        # Upload a valid key
        good_key = self.valid_setup['key']
        handler = self.request({'content': good_key}, role='admin')
        yield handler.post(n)
        yield self.is_set(n, True)

        handler = self.request(role='admin')
        yield self.assertFailure(handler.get(n), errors.MethodNotImplemented)


        # Test key generation
        yield handler.put(n)
        yield self.is_set(n, True)

        # Try delete actions
        yield handler.delete(n)
        yield self.is_set(n, False)

        yield self.set_enabled()
        yield self.assertFailure(handler.delete(n), errors.FailedSanityCheck)
        yield self.assertFailure(handler.put(n), errors.FailedSanityCheck)

    @inlineCallbacks
    def test_cert_file(self):
        n = 'cert'

        yield self.is_set(n, False)
        yield PrivKeyRes.create_file(self.valid_setup[n])

        bad_cert = 'bonk bonk bonk'
        handler = self.request(bad_cert, role='admin')
        yield self.assertFailure(handler.post(n), errors.ValidationError)

        body = {'content': self.valid_setup[n]}
        handler = self.request(body, role='admin')
        yield handler.post(n)
        yield self.is_set(n, True)

        handler = self.request(role='admin')
        yield handler.get(n)
        content = self.responses[-1]
        self.assertEqual(content, self.valid_setup[n])

        yield handler.delete(n)
        yield self.is_set(n, False)

        yield self.assertFailure(handler.get(n), errors.MethodNotImplemented)

    @inlineCallbacks
    def test_chain_file(self):
        handler = self.request({'content': 'bonk bonk bonk'}, role='admin')

        res = yield handler.post(name='cert')


class TestConfigHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = https.ConfigHandler


class TestCSRHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = https.CSRConfigHandler

    @inlineCallbacks
    def test_post(self):
        d = {
           'commonname': 'notreal.ns.com',
           'country': 'IT',
           'province': 'regione',
           'city': 'citta',
           'company': 'azienda',
           'department': 'reparto',
           'email': 'indrizzio@email',
        }

        handler = self.request(d, role='admin')
        res = yield handler.post()

        csr_pem = self.responses[0]['csr_txt']

        pem_csr = crypto.load_certificate_request(SSL.FILETYPE_PEM, csr_pem)

        comps = pem_csr.get_subject().get_components()
        self.assertIn(('CN', 'notreal.ns.com'), comps)
        self.assertIn(('C', 'IT'), comps)
        self.assertIn(('L', 'citta'), comps)
