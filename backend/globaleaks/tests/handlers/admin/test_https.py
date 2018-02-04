# -*- coding: utf-8 -*-
from requests.exceptions import ConnectionError

from OpenSSL import crypto, SSL
from globaleaks.handlers.admin import https
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.state import State
from globaleaks.tests import helpers
from globaleaks.tests.utils import test_tls
from globaleaks.utils.letsencrypt import ChallTok
from twisted.internet.defer import inlineCallbacks, returnValue


@transact
def set_init_params(session, dh_params, hostname='localhost:9999'):
    ConfigFactory(session, 1, 'node').set_val(u'https_dh_params', dh_params)
    ConfigFactory(session, 1, 'node').set_val(u'hostname', hostname)
    State.tenant_cache[1].hostname = 'localhost:9999'


class TestFileHandler(helpers.TestHandler):
    _handler = https.FileHandler

    @inlineCallbacks
    def setUp(self):
        yield super(TestFileHandler, self).setUp()

        self.valid_setup = test_tls.get_valid_setup()
        yield set_init_params(self.valid_setup['dh_params'])

    @inlineCallbacks
    def get_and_check(self, name, is_set):
        handler = self.request(role='admin', handler_cls=https.ConfigHandler)

        response = yield handler.get()

        self.assertEqual(response['files'][name]['set'], is_set)

        returnValue(response)

    @inlineCallbacks
    def test_priv_key_file(self):
        n = 'priv_key'

        yield self.get_and_check(n, False)

        # Try to upload an invalid key
        bad_key = 'donk donk donk donk donk donk'
        handler = self.request({'name': 'priv_key', 'content': bad_key}, role='admin')
        yield self.assertFailure(handler.post(n), errors.InputValidationError)

        # Upload a valid key
        good_key = self.valid_setup['key']
        handler = self.request({'name': 'priv_key', 'content': good_key}, role='admin')

        yield handler.post(n)

        response = yield self.get_and_check(n, True)

        was_generated = response['files']['priv_key']['gen']
        self.assertFalse(was_generated)

        handler = self.request(role='admin')
        yield self.assertFailure(handler.get(n), errors.MethodNotImplemented)

        # Test key generation
        yield handler.put(n)

        response = yield self.get_and_check(n, True)

        was_generated = response['files']['priv_key']['gen']
        self.assertTrue(was_generated)

        # Try delete actions
        yield handler.delete(n)

        yield self.get_and_check(n, False)

    @inlineCallbacks
    def test_cert_file(self):
        n = 'cert'

        yield self.get_and_check(n, False)
        yield https.PrivKeyFileRes.create_file(1, self.valid_setup['key'])

        # Test bad cert
        body = {'name': 'cert', 'content': 'bonk bonk bonk'}
        handler = self.request(body, role='admin')
        yield self.assertFailure(handler.post(n), errors.InputValidationError)

        # Upload a valid cert
        body = {'name': 'cert', 'content': self.valid_setup[n]}
        handler = self.request(body, role='admin')
        yield handler.post(n)

        yield self.get_and_check(n, True)

        handler = self.request(role='admin')
        response = yield handler.get(n)
        self.assertEqual(response, self.valid_setup[n])

        # Finally delete the cert
        yield handler.delete(n)
        yield self.get_and_check(n, False)

    @inlineCallbacks
    def test_chain_file(self):
        n = 'chain'

        yield self.get_and_check(n, False)
        yield https.PrivKeyFileRes.create_file(1, self.valid_setup['key'])
        yield https.CertFileRes.create_file(1, self.valid_setup['cert'])
        State.tenant_cache[1].hostname = 'localhost'

        body = {'name': 'chain', 'content': self.valid_setup[n]}
        handler = self.request(body, role='admin')

        yield handler.post(n)
        yield self.get_and_check(n, True)

        handler = self.request(role='admin')
        response = yield handler.get(n)
        self.assertEqual(response, self.valid_setup[n])

        yield handler.delete(n)
        yield self.get_and_check(n, False)


class TestConfigHandler(helpers.TestHandler):
    _handler = https.ConfigHandler

    @inlineCallbacks
    def test_all_methods(self):
        valid_setup = test_tls.get_valid_setup()

        yield set_init_params(valid_setup['dh_params'])
        yield https.PrivKeyFileRes.create_file(1, valid_setup['key'])
        yield https.CertFileRes.create_file(1, valid_setup['cert'])
        yield https.ChainFileRes.create_file(1, valid_setup['chain'])

        handler = self.request(role='admin')

        response = yield handler.get()
        self.assertTrue(len(response['status']['msg']) > 0)

        # Config is ready to go. So launch the subprocesses.
        yield handler.post()
        response = yield handler.get()
        self.assertTrue(response['enabled'])

        self.test_reactor.pump([50])

        yield handler.put()
        response = yield handler.get()
        self.assertFalse(response['enabled'])


class TestCSRHandler(helpers.TestHandler):
    _handler = https.CSRFileHandler

    @inlineCallbacks
    def test_post(self):
        n = 'csr'

        valid_setup = test_tls.get_valid_setup()
        yield set_init_params(valid_setup['dh_params'])
        yield https.PrivKeyFileRes.create_file(1, valid_setup['key'])
        State.tenant_cache[1].hostname = 'notreal.ns.com'

        d = {
           'country': 'it',
           'province': 'regione',
           'city': 'citta',
           'company': 'azienda',
           'department': 'reparto',
           'email': 'indrizzio@email',
        }

        body = {'name': 'csr', 'content': d}
        handler = self.request(body, role='admin')
        yield handler.post(n)

        response = yield handler.get(n)

        pem_csr = crypto.load_certificate_request(SSL.FILETYPE_PEM, response)

        comps = pem_csr.get_subject().get_components()
        self.assertIn(('CN', 'notreal.ns.com'), comps)
        self.assertIn(('C', 'IT'), comps)
        self.assertIn(('L', 'citta'), comps)


class TestAcmeHandler(helpers.TestHandler):
    _handler = https.AcmeHandler

    @inlineCallbacks
    def test_post(self):
        hostname = 'gl.dl.localhost.com'
        State.tenant_cache[1].hostname = hostname
        valid_setup = test_tls.get_valid_setup()
        yield https.PrivKeyFileRes.create_file(1, valid_setup['key'])

        handler = self.request(role='admin')
        resp = yield handler.post()

        current_le_tos = 'https://letsencrypt.org/documents/LE-SA-v1.2-November-15-2017.pdf'
        self.assertEqual(resp['terms_of_service'], current_le_tos)

    @inlineCallbacks
    def test_put(self):
        valid_setup = test_tls.get_valid_setup()
        yield https.AcmeAccntKeyRes.create_file(1)
        yield https.AcmeAccntKeyRes.save_accnt_uri(1, 'http://localhost:9999')
        yield https.PrivKeyFileRes.create_file(1, valid_setup['key'])
        hostname = 'gl.dl.localhost.com'
        State.tenant_cache[1].hostname = hostname

        body = {
           'name': 'xxx',
           'content': {
               'commonname': hostname,
               'country': 'it',
               'province': 'regione',
               'city': 'citta',
               'company': 'azienda',
               'department': 'reparto',
               'email': 'indrizzio@email',
           }
        }

        handler = self.request(body, role='admin')
        yield self.assertFailure(handler.put(), ConnectionError)


class TestAcmeChallengeHandler(helpers.TestHandler):
    _handler = https.AcmeChallengeHandler

    @inlineCallbacks
    def test_get(self):
        # tmp_chall_dict pollutes scope
        tok = 'yT-RDI9dU7dJPxaTYOgY_YnYYByT4CVAVCC7W3zUDIw'
        v = '{}.5vh2ZRCJGmNUKEEBn-SN6esbMnSl1w8ZT0LDUwexTAM'.format(tok)
        ct = ChallTok(v)

        State.tenant_state[1].acme_tmp_chall_dict.set(tok, ct)

        handler = self.request()
        resp = yield handler.get(tok)

        self.assertEqual(resp, v)
