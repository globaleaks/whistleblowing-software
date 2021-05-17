# -*- coding: utf-8 -*-
from OpenSSL import crypto
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact, tw
from globaleaks.rest import errors, requests
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils import letsencrypt, tls
from globaleaks.utils.log import log


def load_tls_dict(session, tid):
    """
    Transaction for loading the TLS configuration of a tenant

    :param session: An ORM session
    :param tid: A tenant ID
    :return: The serialized TLS configuration for the specified tenant
    """
    node = ConfigFactory(session, tid)

    return {
        'tid': tid,
        'ssl_key': node.get_val('https_key'),
        'ssl_cert': node.get_val('https_cert'),
        'ssl_intermediate': node.get_val('https_chain'),
        'https_enabled': node.get_val('https_enabled'),
        'hostname': node.get_val('hostname'),
    }


def load_tls_dict_list(session):
    return [load_tls_dict(session, tid[0]) for tid in session.query(models.Tenant.id).filter(models.Tenant.active.is_(True))]


def db_create_acme_key(session, tid):
    priv_fact = ConfigFactory(session, tid)

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=Settings.key_bits,
        backend=default_backend()
    )

    key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    priv_fact.set_val('acme', True)
    priv_fact.set_val('acme_accnt_key', key)

    return key


class FileResource(object):
    """
    An interface for interacting with files stored on disk or in the db
    """
    @classmethod
    @transact
    def create_file(session, cls, tid, content):
        raise errors.MethodNotImplemented()

    @classmethod
    def perform_file_action(cls, tid):
        raise errors.MethodNotImplemented()

    @staticmethod
    @transact
    def get_file(session, tid):
        raise errors.MethodNotImplemented()

    @staticmethod
    @transact
    def delete_file(session, tid):
        raise errors.MethodNotImplemented()

    @classmethod
    @transact
    def serialize(cls, session, tid):
        return cls.db_serialize(session)

    @staticmethod
    def db_serialize(session, tid):
        raise errors.MethodNotImplemented()


class PrivKeyFileRes(FileResource):
    validator = tls.PrivKeyValidator

    @classmethod
    @transact
    def create_file(session, cls, tid, raw_key):
        db_cfg = load_tls_dict(session, tid)
        db_cfg['ssl_key'] = raw_key

        config = ConfigFactory(session, tid)
        pkv = cls.validator()
        ok, _ = pkv.validate(db_cfg)
        if ok:
            config.set_val('https_key', raw_key)

        return ok

    @staticmethod
    @transact
    def save_tls_key(session, tid, prv_key):
        ConfigFactory(session, tid).set_val('https_key', prv_key)

    @classmethod
    @inlineCallbacks
    def perform_file_action(cls, tid):
        log.info("Generating the HTTPS key with %d bits" % Settings.key_bits)
        key = yield deferToThread(tls.gen_ecc_key, Settings.key_bits)

        log.debug("Saving the HTTPS key")
        yield cls.save_tls_key(tid, key)

    @staticmethod
    @transact
    def delete_file(session, tid):
        config = ConfigFactory(session, tid)
        config.set_val('https_key', '')

    @staticmethod
    @transact
    def get_file(session, tid):
        return ConfigFactory(session, tid).get_val('https_key')

    @staticmethod
    def db_serialize(session, tid):
        config = ConfigFactory(session, tid)

        return {
            'set': config.get_val('https_key') != ''
        }


class CertFileRes(FileResource):
    validator = tls.CertValidator

    @classmethod
    @transact
    def create_file(session, cls, tid, raw_cert):
        config = ConfigFactory(session, tid)

        db_cfg = load_tls_dict(session, tid)
        db_cfg['ssl_cert'] = raw_cert

        cv = cls.validator()
        ok, _ = cv.validate(db_cfg)
        if ok:
            config.set_val('https_cert', raw_cert)
            State.tenant_cache[tid].https_cert = raw_cert

        return ok

    @staticmethod
    @transact
    def delete_file(session, tid):
        ConfigFactory(session, tid).set_val('https_cert', '')
        State.tenant_cache[tid].https_cert = ''

    @staticmethod
    @transact
    def get_file(session, tid):
        return ConfigFactory(session, tid).get_val('https_cert')

    @staticmethod
    def db_serialize(session, tid):
        c = ConfigFactory(session, tid).get_val('https_cert')
        if not c:
            return {
                'name': 'cert',
                'set': False
            }

        log.err(c)
        c = """{}""".format(c)
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, c)
        expr_date = letsencrypt.convert_asn1_date(x509.get_notAfter())

        return {
            'name': 'cert',
            'issuer': tls.parse_issuer_name(x509),
            'expiration_date': expr_date,
            'set': True,
        }


class ChainFileRes(FileResource):
    validator = tls.ChainValidator

    @classmethod
    @transact
    def create_file(session, cls, tid, raw_chain):
        config = ConfigFactory(session, tid)

        db_cfg = load_tls_dict(session, tid)
        db_cfg['ssl_intermediate'] = raw_chain

        cv = cls.validator()
        ok, _ = cv.validate(db_cfg)
        if ok:
            config.set_val('https_chain', raw_chain)

        return ok

    @staticmethod
    @transact
    def delete_file(session, tid):
        ConfigFactory(session, tid).set_val('https_chain', '')

    @staticmethod
    @transact
    def get_file(session, tid):
        return ConfigFactory(session, tid).get_val('https_chain')

    @staticmethod
    def db_serialize(session, tid):
        c = ConfigFactory(session, tid).get_val('https_chain')
        if not c:
            return {
                'name': 'chain',
                'set': False
            }

        c = tls.split_pem_chain(c)[0]
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, c)
        expr_date = letsencrypt.convert_asn1_date(x509.get_notAfter())

        return {
            'name': 'chain',
            'issuer': tls.parse_issuer_name(x509),
            'expiration_date': expr_date,
            'set': True
        }


class CsrFileRes(FileResource):
    @classmethod
    @transact
    def create_file(session, cls, tid, raw_csr):
        ConfigFactory(session, tid).set_val('https_csr', raw_csr)

        return True

    @staticmethod
    @transact
    def delete_file(session, tid):
        ConfigFactory(session, tid).set_val('https_csr', '')

    @staticmethod
    @transact
    def get_file(session, tid):
        return ConfigFactory(session, tid).get_val('https_csr')

    @staticmethod
    def db_serialize(session, tid):
        csr = ConfigFactory(session, tid).get_val('https_csr')
        return {
            'name': 'csr',
            'set': len(csr) != 0
        }


class FileHandler(BaseHandler):
    check_roles = 'admin'

    mapped_file_resources = {
        'key': PrivKeyFileRes,
        'cert': CertFileRes,
        'chain': ChainFileRes,
        'csr': CsrFileRes,
    }

    def get_file_res_or_raise(self, name):
        if name not in self.mapped_file_resources:
            raise errors.MethodNotImplemented()

        return self.mapped_file_resources[name]

    def delete(self, name):
        return self.get_file_res_or_raise(name).delete_file(self.request.tid)

    @inlineCallbacks
    def post(self, name):
        req = self.validate_message(self.request.content.read(),
                                    requests.AdminTLSCfgFileResourceDesc)

        file_res_cls = self.get_file_res_or_raise(name)

        ok = yield file_res_cls.create_file(self.request.tid, req['content'])
        if not ok:
            raise errors.InputValidationError()

    @inlineCallbacks
    def put(self, name):
        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.perform_file_action(self.request.tid)

    def get(self, name):
        return self.get_file_res_or_raise(name).get_file(self.request.tid)


@transact
def serialize_https_config_summary(session, tid):
    config = ConfigFactory(session, tid)

    file_summaries = {}
    for key, file_res_cls in FileHandler.mapped_file_resources.items():
        file_summaries[key] = file_res_cls.db_serialize(session, tid)

    return {
        'enabled': config.get_val('https_enabled'),
        'files': file_summaries,
        'acme': config.get_val('acme')
    }


@transact
def try_to_enable_https(session, tid):
    config = ConfigFactory(session, tid)

    cv = tls.ChainValidator()
    tls_config = load_tls_dict(session, tid)
    tls_config['https_enabled'] = False

    ok, _ = cv.validate(tls_config)
    if not ok:
        raise errors.InputValidationError()

    config.set_val('https_enabled', True)
    State.tenant_cache[tid].https_enabled = True
    State.snimap.load(tid, tls_config)


@transact
def disable_https(session, tid):
    ConfigFactory(session, tid).set_val('https_enabled', False)
    State.tenant_cache[tid].https_enabled = False
    State.snimap.unload(tid)


@transact
def reset_https_config(session, tid):
    config = ConfigFactory(session, tid)
    config.set_val('https_enabled', False)
    config.set_val('https_key', '')
    config.set_val('https_cert', '')
    config.set_val('https_chain', '')
    config.set_val('https_csr', '')
    config.set_val('acme', False)
    config.set_val('acme_accnt_key', '')

    State.tenant_cache[tid].https_enabled = False


class ConfigHandler(BaseHandler):
    check_roles = 'admin'

    def get(self):
        return serialize_https_config_summary(self.request.tid)

    def post(self):
        return try_to_enable_https(self.request.tid)

    def put(self):
        return disable_https(self.request.tid)

    def delete(self):
        return reset_https_config(self.request.tid)


class CSRFileHandler(FileHandler):
    check_roles = 'admin'

    @inlineCallbacks
    def post(self, name):
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminCSRFileDesc)

        desc = request['content']
        csr_fields = {
            'C': desc['country'].upper(),
            'ST': desc['province'],
            'L': desc['city'],
            'O': desc['company'],
            'OU': desc['department'],
            'CN': State.tenant_cache[self.request.tid].hostname,
            # TODO use current admin user mail
            'emailAddress': desc['email'],
        }

        csr_txt = yield self.perform_action(self.request.tid, csr_fields)

        file_res_cls = self.get_file_res_or_raise(name)

        ok = yield file_res_cls.create_file(self.request.tid, csr_txt)
        if not ok:
            raise errors.InputValidationError()

    @staticmethod
    @transact
    def perform_action(session, tid, csr_fields):
        db_cfg = load_tls_dict(session, tid)

        pkv = tls.PrivKeyValidator()
        ok, _ = pkv.validate(db_cfg)
        if not ok:
            raise errors.InputValidationError()

        key_pair = db_cfg['ssl_key']
        try:
            csr_txt = tls.gen_x509_csr_pem(key_pair, csr_fields, Settings.csr_sign_bits)
            log.debug("Generated a new CSR")
            return csr_txt
        except Exception as e:
            log.err(e)
            raise errors.InputValidationError('CSR gen failed')


class AcmeAccntKeyRes:
    @classmethod
    @transact
    def create_file(session, cls, tid):
        log.info("Generating an ACME account key with %d bits" % Settings.key_bits)

        return db_create_acme_key(session, tid)


def db_acme_cert_request(session, tid):
    priv_fact = ConfigFactory(session, tid)
    hostname = State.tenant_cache[tid].hostname

    raw_accnt_key = priv_fact.get_val('acme_accnt_key')
    if not raw_accnt_key:
        raw_accnt_key = db_create_acme_key(session, tid)

    if isinstance(raw_accnt_key, str):
        raw_accnt_key = raw_accnt_key.encode()

    accnt_key = serialization.load_pem_private_key(raw_accnt_key,
                                                   password=None,
                                                   backend=default_backend())

    key = priv_fact.get_val('https_key')

    cert_str, chain_str = letsencrypt.request_new_certificate(hostname,
                                                              accnt_key,
                                                              key,
                                                              State.tenant_state[tid].acme_tmp_chall_dict,
                                                              Settings.acme_directory_url)

    priv_fact.set_val('https_cert', cert_str)
    priv_fact.set_val('https_chain', chain_str)
    State.tenant_cache[tid].https_cert = cert_str
    State.tenant_cache[tid].https_chain = chain_str


class AcmeHandler(BaseHandler):
    check_roles = 'admin'

    @inlineCallbacks
    def post(self):
        accnt_key = yield AcmeAccntKeyRes.create_file(self.request.tid)
        yield tw(db_acme_cert_request, self.request.tid)


class AcmeChallengeHandler(BaseHandler):
    check_roles = 'any'

    def get(self, token):
        tmp_chall_dict = State.tenant_state[self.request.tid].acme_tmp_chall_dict
        if token in tmp_chall_dict:
            log.info('Responding to valid .well-known request [%d]', self.request.tid)
            return tmp_chall_dict[token].tok

        raise errors.ResourceNotFound
