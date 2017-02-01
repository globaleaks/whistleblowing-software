import unittest
import os

import twisted
from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor, defer
from OpenSSL import crypto, SSL

from globaleaks.handlers.admin.config import tls
from globaleaks.tests import helpers


class TestCryptoFuncs(unittest.TestCase):
    def test_it_all(self):
        key_pair = tls.gen_RSA_key()

        d = {
         'CN': 'fakedom.blah.blah',
         'O': 'widgets-R-us',
        }

        csr = tls.gen_x509_csr(key_pair, d)
        pem_csr = crypto.dump_certificate_request(SSL.FILETYPE_PEM, csr)
        #print(pem_csr)


from twisted.trial.unittest import TestCase


class TestHTTPSWorkers(unittest.TestCase):
    def test_launch_workers(self):
        d = {
            'cert': '',
            #'chain': '',
            #'dh': '',
            'priv_key': '',
        }

        for key in d.keys():
            with open(os.path.join(helpers.KEYS_PATH, 'https', key+'.pem')) as f:
                d[key] = f.read()

        pool = tls.tls_master.launch_workers({}, d['priv_key'], d['cert'], '', '')

        d = defer.gatherResults([p.deferredConnect for p in pool])
        def test_cb(ignored):
            print('Resolving final defered', ignored)

        d.addCallback(test_cb)
        return d

        #from twisted.internet import reactor
        #from IPython import embed; embed()
        #import time; time.sleep(60)


class TestCertFileHandler(helpers.TestHandlerWithPopulatedDB):
    
    _handler = tls.CertFileHandler

    def test_post(self):
        # TODO TODO TODO 
        handler = self.request(d, role='admin')
        res = handler.post()
        # TODO TODO TODO



class TestCSRHandler(helpers.TestHandlerWithPopulatedDB):
    _handler = tls.CSRConfigHandler

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
        self.assertIn(('C', 'IT'), subject.comps)
        self.assertIn(('L', 'citta'), subject.comps)
