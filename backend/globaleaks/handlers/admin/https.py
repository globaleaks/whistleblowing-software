# -*- coding: utf-8 -*-
import urlparse

from OpenSSL import crypto
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.error import ConnectError
from twisted.internet.threads import deferToThread
from twisted.web.client import readBody

from globaleaks.handlers.base import BaseHandler, HANDLER_EXEC_TIME_THRESHOLD
from globaleaks.models.config import PrivateFactory, load_tls_dict
from globaleaks.orm import transact, transact_sync
from globaleaks.rest import errors, requests
from globaleaks.settings import GLSettings
from globaleaks.utils import letsencrypt
from globaleaks.utils import tls
from globaleaks.utils.tempdict import TempDict
from globaleaks.utils.utility import datetime_to_ISO8601, format_cert_expr_date, log


# Access auth tokens expire after a 5 minutes
tmp_chall_dict = TempDict(300)


class FileResource(object):
    """
    An interface for interacting with files stored on disk or in the db
    """
    @classmethod
    @transact
    def create_file(store, content):
        raise errors.MethodNotImplemented()

    @staticmethod
    def perform_file_action():
        raise errors.MethodNotImplemented()

    @staticmethod
    @transact
    def get_file(store):
        """
        :rtype: A `unicode` string
        """
        raise errors.MethodNotImplemented()

    @staticmethod
    @transact
    def delete_file(store):
        raise errors.MethodNotImplemented()

    @classmethod
    @transact
    def serialize(cls, store):
        return cls.db_serialize(store)

    @staticmethod
    def db_serialize(store):
        """
        :rtype: A `dict` to be converted into JSON for delivery to a client
        """
        raise errors.MethodNotImplemented()

    @staticmethod
    @transact
    def should_gen_dh_params(store):
        return PrivateFactory(store).get_val('https_dh_params') == u''

    @staticmethod
    @transact
    def save_dh_params(store, dh_params):
        PrivateFactory(store).set_val('https_dh_params', dh_params)

    @classmethod
    @inlineCallbacks
    def generate_dh_params_if_missing(cls):
        gen_dh = yield FileResource.should_gen_dh_params()
        if gen_dh:
            log.info("Generating the HTTPS DH params with %d bits" % GLSettings.key_bits)
            dh_params = yield deferToThread(tls.gen_dh_params, GLSettings.key_bits)

            log.info("Storing the HTTPS DH params")
            yield cls.save_dh_params(dh_params)


class PrivKeyFileRes(FileResource):
    validator = tls.PrivKeyValidator

    @classmethod
    @transact
    def create_file(store, cls, raw_key):
        db_cfg = load_tls_dict(store)
        db_cfg['ssl_key'] = raw_key

        prv_fact = PrivateFactory(store)
        pkv = cls.validator()
        ok, _ = pkv.validate(db_cfg)
        if ok:
            prv_fact.set_val('https_priv_key', raw_key)
            prv_fact.set_val('https_priv_gen', False)
        else:
            log.debug('Key validation failed')

        return ok

    @staticmethod
    @transact
    def save_tls_key(store, prv_key):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_priv_key', prv_key)
        prv_fact.set_val('https_priv_gen', True)

    @classmethod
    @inlineCallbacks
    def perform_file_action(cls):
        log.info("Generating the HTTPS key with %d bits" % GLSettings.key_bits)
        key = yield deferToThread(tls.gen_rsa_key, GLSettings.key_bits)

        log.debug("Saving the HTTPS key")
        yield cls.save_tls_key(key)

    @staticmethod
    @transact
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_priv_key', u'')
        prv_fact.set_val('https_priv_gen', False)

    @staticmethod
    def db_serialize(store):
        prv_fact = PrivateFactory(store)

        return {
            'set': prv_fact.get_val('https_priv_key') != u'',
            'gen': prv_fact.get_val('https_priv_gen')
        }


class CertFileRes(FileResource):
    validator = tls.CertValidator

    @classmethod
    @transact
    def create_file(store, cls, raw_cert):
        prv_fact = PrivateFactory(store)

        db_cfg = load_tls_dict(store)
        db_cfg['ssl_cert'] = raw_cert

        cv = cls.validator()
        ok, _ = cv.validate(db_cfg)
        if ok:
            prv_fact.set_val('https_cert', raw_cert)
            GLSettings.memory_copy.https_cert = raw_cert
        else:
            log.err("Cert validation failed")
        return ok

    @staticmethod
    @transact
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_cert', u'')
        GLSettings.memory_copy.https_cert = ''

    @staticmethod
    @transact
    def get_file(store):
        prv_fact = PrivateFactory(store)
        return prv_fact.get_val('https_cert')

    @staticmethod
    def db_serialize(store):
        c = PrivateFactory(store).get_val('https_cert')
        if len(c) == 0:
            return {'name': 'cert', 'set': False}

        x509 = crypto.load_certificate(FILETYPE_PEM, c)
        expr_date = format_cert_expr_date(x509.get_notAfter())

        return {
            'name': 'cert',
            'issuer': tls.parse_issuer_name(x509),
            'expiration_date': datetime_to_ISO8601(expr_date),
            'set': True,
        }


class ChainFileRes(FileResource):
    validator = tls.ChainValidator

    @classmethod
    @transact
    def create_file(store, cls, raw_chain):
        prv_fact = PrivateFactory(store)

        db_cfg = load_tls_dict(store)
        db_cfg['ssl_intermediate'] = raw_chain

        cv = cls.validator()
        ok, _ = cv.validate(db_cfg)
        if ok:
            prv_fact.set_val('https_chain', raw_chain)
        else:
            log.debug('Chain validation failed')
        return ok

    @staticmethod
    @transact
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_chain', u'')

    @staticmethod
    @transact
    def get_file(store):
        prv_fact = PrivateFactory(store)
        return prv_fact.get_val('https_chain')

    @staticmethod
    def db_serialize(store):
        c = PrivateFactory(store).get_val('https_chain')
        if len(c) == 0:
            return {'name': 'chain', 'set': False}

        x509 = load_certificate(FILETYPE_PEM, c)
        expr_date = format_cert_expr_date(x509.get_notAfter())

        return {
            'name': 'chain',
            'issuer': tls.parse_issuer_name(x509),
            'expiration_date': datetime_to_ISO8601(expr_date),
            'set': True,
        }


class CsrFileRes(FileResource):
    @classmethod
    @transact
    def create_file(store, cls, raw_csr):
        prv_fact = PrivateFactory(store)

        prv_fact.set_val('https_csr', raw_csr)

        return True

    @staticmethod
    @transact
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_csr', u'')

    @staticmethod
    @transact
    def get_file(store):
        prv_fact = PrivateFactory(store)
        return prv_fact.get_val('https_csr')

    @staticmethod
    def db_serialize(store):
        c = PrivateFactory(store).get_val('https_csr')
        if len(c) == 0:
            return {'name': 'csr', 'set': False}

        return {
            'name': 'csr',
            'set': True,
        }


class FileHandler(BaseHandler):
    check_roles = 'admin'

    mapped_file_resources = {
        'priv_key': PrivKeyFileRes,
        'cert':  CertFileRes,
        'chain': ChainFileRes,
        'csr': CsrFileRes,
    }

    # TODO move generate_dh_params to priv_key file handler to free handler timing
    # analysis on the mapped file resources.
    handler_exec_time_threshold = 10*HANDLER_EXEC_TIME_THRESHOLD

    def get_file_res_or_raise(self, name):
        if name not in self.mapped_file_resources:
            raise errors.MethodNotImplemented()

        return self.mapped_file_resources[name]

    @BaseHandler.https_disabled
    def delete(self, name):
        file_res_cls = self.get_file_res_or_raise(name)
        return file_res_cls.delete_file()

    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self, name):
        req = self.validate_message(self.request.content.read(),
                                    requests.AdminTLSCfgFileResourceDesc)

        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.generate_dh_params_if_missing()

        ok = yield file_res_cls.create_file(req['content'])
        if not ok:
            raise errors.ValidationError()

    @BaseHandler.https_disabled
    @inlineCallbacks
    def put(self, name):
        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.generate_dh_params_if_missing()

        yield file_res_cls.perform_file_action()

    @BaseHandler.https_disabled
    def get(self, name):
        file_res_cls = self.get_file_res_or_raise(name)

        return file_res_cls.get_file()


@transact
def serialize_https_config_summary(store):
    prv_fact = PrivateFactory(store)

    file_summaries = {}

    for key, file_res_cls in FileHandler.mapped_file_resources.items():
        file_summaries[key] = file_res_cls.db_serialize(store)

    ret = {
      'enabled': prv_fact.get_val('https_enabled'),
      'running': GLSettings.appstate.process_supervisor.is_running(),
      'status': GLSettings.appstate.process_supervisor.get_status(),
      'files': file_summaries,
      'acme': prv_fact.get_val('acme')
    }

    return ret


@transact
def try_to_enable_https(store):
    prv_fact = PrivateFactory(store)

    cv = tls.ChainValidator()
    db_cfg = load_tls_dict(store)
    db_cfg['https_enabled'] = False

    ok, err = cv.validate(db_cfg)
    if ok:
        prv_fact.set_val('https_enabled', True)
        GLSettings.memory_copy.private.https_enabled = True
    else:
        raise err

@transact
def disable_https(store):
    prv_fact = PrivateFactory(store)
    log.debug('Disabling https on the node.')
    prv_fact.set_val('https_enabled', False)


class ConfigHandler(BaseHandler):
    check_roles = 'admin'

    def get(self):
        return serialize_https_config_summary()

    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self):
        try:
            yield try_to_enable_https()
            yield GLSettings.appstate.process_supervisor.maybe_launch_https_workers()
        except Exception as e:
            log.err(e)
            raise errors.InternalServerError(str(e))

    @BaseHandler.https_enabled
    @inlineCallbacks
    def put(self):
        """
        Disables HTTPS config and shutdown subprocesses.
        """
        yield disable_https()
        GLSettings.memory_copy.private.https_enabled = False
        GLSettings.appstate.process_supervisor.shutdown()

    @inlineCallbacks
    def delete(self):
        yield disable_https()
        GLSettings.memory_copy.private.https_enabled = False
        GLSettings.appstate.process_supervisor.shutdown()
        yield _delete_all_cfg()


@transact
def _delete_all_cfg(store):
    prv_fact = PrivateFactory(store)
    prv_fact.set_val('https_enabled', False)
    prv_fact.set_val('https_priv_gen', False)
    prv_fact.set_val('https_priv_key', '')
    prv_fact.set_val('https_cert', '')
    prv_fact.set_val('https_chain', '')
    prv_fact.set_val('https_csr', '')
    prv_fact.set_val('acme', False)
    prv_fact.set_val('acme_accnt_key', '')
    prv_fact.set_val('acme_accnt_uri', '')


class CSRFileHandler(FileHandler):
    check_roles = 'admin'

    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self, name):
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminCSRFileDesc)

        desc = request['content']

        csr_fields = {
                'C':  desc['country'].upper(),
                'ST': desc['province'],
                'L':  desc['city'],
                'O':  desc['company'],
                'OU': desc['department'],
                'CN': GLSettings.memory_copy.hostname,
                'emailAddress': desc['email'], # TODO use current admin user mail
        }

        csr_txt = yield self.perform_action(csr_fields)

        file_res_cls = self.get_file_res_or_raise(name)

        ok = yield file_res_cls.create_file(csr_txt)
        if not ok:
            raise errors.ValidationError()

    @staticmethod
    @transact
    def perform_action(store, csr_fields):
        db_cfg = load_tls_dict(store)

        pkv = tls.PrivKeyValidator()
        ok, err = pkv.validate(db_cfg)
        if not ok or not err is None:
            raise err

        key_pair = db_cfg['ssl_key']
        try:
            csr_txt = tls.gen_x509_csr_pem(key_pair, csr_fields, GLSettings.csr_sign_bits)
            log.debug("Generated a new CSR")
            return csr_txt
        except Exception as e:
            log.err(e)
            raise errors.ValidationError('CSR gen failed')


class AcmeAccntKeyRes:
    @classmethod
    @transact
    def create_file(store, cls):
        log.info("Generating an ACME account key with %d bits" % GLSettings.key_bits)

        # NOTE key size is hard coded to align with minimum CA requirements
        # TODO change format to OpenSSL key to normalize types of keys used
        priv_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend())

        log.debug("Saving the ACME key")
        b = priv_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
        )

        PrivateFactory(store).set_val('acme', True)
        PrivateFactory(store).set_val('acme_accnt_key', b)

        return priv_key

    @classmethod
    @transact
    def save_accnt_uri(store, cls, uri):
        PrivateFactory(store).set_val('acme_accnt_uri', uri)


@transact
def can_perform_acme_run(store):
    prv_fact = PrivateFactory(store)
    acme = prv_fact.get_val('acme')
    no_cert_set = prv_fact.get_val('https_cert') == u''
    return acme and no_cert_set


@transact
def is_acme_configured(store):
    prv_fact = PrivateFactory(store)
    acme = prv_fact.get_val('acme')
    cert_set = prv_fact.get_val('https_cert') != u''
    return acme and cert_set


@transact
def can_perform_acme_renewal(store):
    a = is_acme_configured(store)
    b = PrivateFactory(store).get_val('https_enabled')
    c = PrivateFactory(store).get_val('https_cert')
    return a and b and c


class AcmeHandler(BaseHandler):
    check_roles='admin'

    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self):
        accnt_key = yield AcmeAccntKeyRes.create_file()

        # TODO should throw if key is already registered
        regr_uri, tos_url = letsencrypt.register_account_key(GLSettings.acme_directory_url, accnt_key)

        yield AcmeAccntKeyRes.save_accnt_uri(regr_uri)

        returnValue({'terms_of_service': tos_url})

    @BaseHandler.https_disabled
    @inlineCallbacks
    def put(self):
        is_ready = yield can_perform_acme_run()
        if not is_ready:
            raise errors.ForbiddenOperation()

        yield deferToThread(acme_cert_issuance)


@transact_sync
def acme_cert_issuance(store):
    return db_acme_cert_issuance(store)


def db_acme_cert_issuance(store):
    hostname = GLSettings.memory_copy.hostname

    raw_accnt_key = PrivateFactory(store).get_val('acme_accnt_key')
    accnt_key = serialization.load_pem_private_key(str(raw_accnt_key),
                                                   password=None,
                                                   backend=default_backend())


    priv_key = PrivateFactory(store).get_val('https_priv_key')
    regr_uri = PrivateFactory(store).get_val('acme_accnt_uri')

    csr_fields = {'CN': hostname}
    # NOTE sha256 is always employed as hash fnc here.
    csr = tls.gen_x509_csr(priv_key, csr_fields, 256)

    # Run ACME registration all the way to resolution
    cert_str, chain_str = letsencrypt.run_acme_reg_to_finish(hostname,
                                                             regr_uri,
                                                             accnt_key,
                                                             priv_key,
                                                             csr,
                                                             tmp_chall_dict,
                                                             GLSettings.acme_directory_url)

    PrivateFactory(store).set_val('https_cert', cert_str)
    PrivateFactory(store).set_val('https_chain', chain_str)


class AcmeChallResolver(BaseHandler):
    check_roles = 'unauthenticated'

    def get(self, token):
        if token in tmp_chall_dict:
            log.info('Responding to valid .well-known request')
            return tmp_chall_dict[token].tok
        raise errors.ResourceNotFound


class HostnameTestHandler(BaseHandler):
    check_roles = 'admin'

    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self):
        if GLSettings.memory_copy.hostname == '':
            raise errors.ValidationError('hostname is not set')

        net_agent = GLSettings.get_agent()

        t = ('http', GLSettings.memory_copy.hostname, 'robots.txt', None, None)
        url = bytes(urlparse.urlunsplit(t))
        try:
            resp = yield net_agent.request('GET', url)
            body = yield readBody(resp)

            server_h = resp.headers.getRawHeaders('Server', [None])[-1].lower()
            if not body.startswith('User-agent: *') or server_h != 'globaleaks':
                raise EnvironmentError('Response unexpected')
        except (EnvironmentError, ConnectError) as e:
            log.err(e)
            raise errors.ExternalResourceError()
