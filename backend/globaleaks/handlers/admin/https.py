# -*- coding: utf-8 -*-
from OpenSSL import crypto
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread

from globaleaks import models
from globaleaks.handlers.base import BaseHandler, HANDLER_EXEC_TIME_THRESHOLD
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils import letsencrypt, tls
from globaleaks.utils.utility import datetime_to_ISO8601, format_cert_expr_date, log


def load_tls_dict(session, tid):
    """
    A quick and dirty function to grab all of the tls config for use in subprocesses
    """
    node = ConfigFactory(session, tid, 'node')

    return {
        'ssl_key': node.get_val(u'https_priv_key'),
        'ssl_cert': node.get_val(u'https_cert'),
        'ssl_intermediate': node.get_val(u'https_chain'),
        'ssl_dh': node.get_val(u'https_dh_params'),
        'https_enabled': node.get_val(u'https_enabled'),
        'hostname': node.get_val(u'hostname'),
    }


def load_tls_dict_list(session):
    return [load_tls_dict(session, tid[0]) for tid in session.query(models.Tenant.id)]


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
        """
        :rtype: A `unicode` string
        """
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
        """
        :rtype: A `dict` to be converted into JSON for delivery to a client
        """
        raise errors.MethodNotImplemented()

    @staticmethod
    @transact
    def should_gen_dh_params(session, tid):
        return ConfigFactory(session, tid, 'node').get_val(u'https_dh_params') == u''

    @staticmethod
    @transact
    def save_dh_params(session, tid, dh_params):
        ConfigFactory(session, tid, 'node').set_val(u'https_dh_params', dh_params)

    @classmethod
    @inlineCallbacks
    def generate_dh_params_if_missing(cls, tid):
        gen_dh = yield FileResource.should_gen_dh_params(tid)
        if gen_dh:
            log.info("Generating the HTTPS DH params with %d bits" % Settings.key_bits)
            dh_params = yield deferToThread(tls.gen_dh_params, Settings.key_bits)

            log.info("Storing the HTTPS DH params")
            yield cls.save_dh_params(tid, dh_params)


class PrivKeyFileRes(FileResource):
    validator = tls.PrivKeyValidator

    @classmethod
    @transact
    def create_file(session, cls, tid, raw_key):
        db_cfg = load_tls_dict(session, tid)
        db_cfg['ssl_key'] = raw_key

        config = ConfigFactory(session, tid, 'node')
        pkv = cls.validator()
        ok, _ = pkv.validate(db_cfg)
        if ok:
            config.set_val(u'https_priv_key', raw_key)
            config.set_val(u'https_priv_gen', False)

        return ok

    @staticmethod
    @transact
    def save_tls_key(session, tid, prv_key):
        config = ConfigFactory(session, tid, 'node')
        config.set_val(u'https_priv_key', prv_key)
        config.set_val(u'https_priv_gen', True)

    @classmethod
    @inlineCallbacks
    def perform_file_action(cls, tid):
        log.info("Generating the HTTPS key with %d bits" % Settings.key_bits)
        key = yield deferToThread(tls.gen_rsa_key, Settings.key_bits)

        log.debug("Saving the HTTPS key")
        yield cls.save_tls_key(tid, key)

    @staticmethod
    @transact
    def delete_file(session, tid):
        config = ConfigFactory(session, tid, 'node')
        config.set_val(u'https_priv_key', u'')
        config.set_val(u'https_priv_gen', False)

    @staticmethod
    def db_serialize(session, tid):
        config = ConfigFactory(session, tid, 'node')

        return {
            'set': config.get_val(u'https_priv_key') != u'',
            'gen': config.get_val(u'https_priv_gen')
        }


class CertFileRes(FileResource):
    validator = tls.CertValidator

    @classmethod
    @transact
    def create_file(session, cls, tid, raw_cert):
        config = ConfigFactory(session, tid, 'node')

        db_cfg = load_tls_dict(session, tid)
        db_cfg['ssl_cert'] = raw_cert

        cv = cls.validator()
        ok, _ = cv.validate(db_cfg)
        if ok:
            config.set_val(u'https_cert', raw_cert)
            State.tenant_cache[tid].https_cert = raw_cert

        return ok

    @staticmethod
    @transact
    def delete_file(session, tid):
        ConfigFactory(session, tid, 'node').set_val(u'https_cert', u'')
        State.tenant_cache[tid].https_cert = ''

    @staticmethod
    @transact
    def get_file(session, tid):
        return ConfigFactory(session, tid, 'node').get_val(u'https_cert')

    @staticmethod
    def db_serialize(session, tid):
        c = ConfigFactory(session, tid, 'node').get_val(u'https_cert')
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
    def create_file(session, cls, tid, raw_chain):
        config = ConfigFactory(session, tid, 'node')

        db_cfg = load_tls_dict(session, tid)
        db_cfg['ssl_intermediate'] = raw_chain

        cv = cls.validator()
        ok, _ = cv.validate(db_cfg)
        if ok:
            config.set_val(u'https_chain', raw_chain)

        return ok

    @staticmethod
    @transact
    def delete_file(session, tid):
        ConfigFactory(session, tid, 'node').set_val(u'https_chain', u'')

    @staticmethod
    @transact
    def get_file(session, tid):
        return ConfigFactory(session, tid, 'node').get_val(u'https_chain')

    @staticmethod
    def db_serialize(session, tid):
        c = ConfigFactory(session, tid, 'node').get_val(u'https_chain')
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
    def create_file(session, cls, tid, raw_csr):
        ConfigFactory(session, tid, 'node').set_val(u'https_csr', raw_csr)

        return True

    @staticmethod
    @transact
    def delete_file(session, tid):
        ConfigFactory(session, tid, 'node').set_val(u'https_csr', u'')

    @staticmethod
    @transact
    def get_file(session, tid):
        return ConfigFactory(session, tid, 'node').get_val(u'https_csr')

    @staticmethod
    def db_serialize(session, tid):
        csr = ConfigFactory(session, tid, 'node').get_val(u'https_csr')
        return {'name': 'csr', 'set': len(csr) != 0}


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

    def delete(self, name):
        return self.get_file_res_or_raise(name).delete_file(self.request.tid)

    @inlineCallbacks
    def post(self, name):
        req = self.validate_message(self.request.content.read(),
                                    requests.AdminTLSCfgFileResourceDesc)

        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.generate_dh_params_if_missing(self.request.tid)

        ok = yield file_res_cls.create_file(self.request.tid, req['content'])
        if not ok:
            raise errors.InputValidationError()

    @inlineCallbacks
    def put(self, name):
        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.generate_dh_params_if_missing(self.request.tid)

        yield file_res_cls.perform_file_action(self.request.tid)

    def get(self, name):
        return self.get_file_res_or_raise(name).get_file(self.request.tid)


@transact
def serialize_https_config_summary(session, tid):
    config = ConfigFactory(session, tid, 'node')

    file_summaries = {}
    for key, file_res_cls in FileHandler.mapped_file_resources.items():
        file_summaries[key] = file_res_cls.db_serialize(session, tid)

    return {
      'enabled': config.get_val(u'https_enabled'),
      'running': State.process_supervisor.is_running(),
      'status': State.process_supervisor.get_status(),
      'files': file_summaries,
      'acme': config.get_val(u'acme')
    }


@transact
def try_to_enable_https(session, tid):
    config = ConfigFactory(session, tid, 'node')

    cv = tls.ChainValidator()
    db_cfg = load_tls_dict(session, tid)
    db_cfg['https_enabled'] = False

    ok, err = cv.validate(db_cfg)
    if ok:
        config.set_val(u'https_enabled', True)
        State.tenant_cache[tid].https_enabled = True
    else:
        raise err


@transact
def disable_https(session, tid):
    ConfigFactory(session, tid, 'node').set_val(u'https_enabled', False)
    State.tenant_cache[tid].https_enabled = False


@transact
def reset_https_config(session, tid):
    config = ConfigFactory(session, tid, 'node')
    config.set_val(u'https_enabled', False)
    config.set_val(u'https_priv_gen', False)
    config.set_val(u'https_priv_key', '')
    config.set_val(u'https_cert', '')
    config.set_val(u'https_chain', '')
    config.set_val(u'https_csr', '')
    config.set_val(u'acme', False)
    config.set_val(u'acme_accnt_key', '')
    config.set_val(u'acme_accnt_uri', '')

    State.tenant_cache[tid].https_enabled = False


class ConfigHandler(BaseHandler):
    check_roles = 'admin'

    def get(self):
        return serialize_https_config_summary(self.request.tid)

    @inlineCallbacks
    def post(self):
        yield State.process_supervisor.shutdown()
        yield try_to_enable_https(self.request.tid)
        yield State.process_supervisor.maybe_launch_https_workers()

    @inlineCallbacks
    def put(self):
        """
        Disables HTTPS config and shutdown subprocesses.
        """
        yield disable_https(self.request.tid)
        yield State.process_supervisor.shutdown()
        yield State.process_supervisor.maybe_launch_https_workers()

    @inlineCallbacks
    def delete(self):
        yield reset_https_config(self.request.tid)
        yield State.process_supervisor.shutdown()
        yield State.process_supervisor.maybe_launch_https_workers()


class CSRFileHandler(FileHandler):
    check_roles = 'admin'

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
                'CN': State.tenant_cache[self.request.tid].hostname,
                'emailAddress': desc['email'], # TODO use current admin user mail
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
        ok, err = pkv.validate(db_cfg)
        if not ok or not err is None:
            raise err

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

        priv_fact = ConfigFactory(session, tid, 'node')

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

        priv_fact.set_val(u'acme', True)
        priv_fact.set_val(u'acme_accnt_key', b)

        return priv_key

    @classmethod
    @transact
    def save_accnt_uri(session, cls, tid, uri):
        ConfigFactory(session, tid, 'node').set_val(u'acme_accnt_uri', uri)


@transact
def can_perform_acme_run(session, tid):
    config = ConfigFactory(session, tid, 'node')
    acme = config.get_val(u'acme')
    no_cert_set = config.get_val(u'https_cert') == u''
    return acme and no_cert_set


@transact
def is_acme_configured(session, tid):
    config = ConfigFactory(session, tid, 'node')
    acme = config.get_val(u'acme')
    cert_set = config.get_val(u'https_cert') != u''
    return acme and cert_set


@transact
def can_perform_acme_renewal(session, tid):
    priv_fact = ConfigFactory(session, tid, 'node')
    a = is_acme_configured(session, tid)
    b = priv_fact.get_val(u'https_enabled')
    c = priv_fact.get_val(u'https_cert')
    return a and b and c


def db_acme_cert_issuance(session, tid):
    priv_fact = ConfigFactory(session, tid, 'node')
    hostname = State.tenant_cache[tid].hostname

    raw_accnt_key = priv_fact.get_val(u'acme_accnt_key')
    accnt_key = serialization.load_pem_private_key(str(raw_accnt_key),
                                                   password=None,
                                                   backend=default_backend())


    priv_key = priv_fact.get_val(u'https_priv_key')
    regr_uri = priv_fact.get_val(u'acme_accnt_uri')

    csr_fields = {'CN': hostname}
    # NOTE sha256 is always employed as hash fnc here.
    csr = tls.gen_x509_csr(priv_key, csr_fields, 256)

    tmp_chall_dict = State.tenant_state[tid].acme_tmp_chall_dict

    # Run ACME registration all the way to resolution
    cert_str, chain_str = letsencrypt.run_acme_reg_to_finish(hostname,
                                                             regr_uri,
                                                             accnt_key,
                                                             priv_key,
                                                             csr,
                                                             tmp_chall_dict,
                                                             Settings.acme_directory_url)

    priv_fact.set_val(u'https_cert', cert_str)
    priv_fact.set_val(u'https_chain', chain_str)
    State.tenant_cache[tid].https_cert = cert_str
    State.tenant_cache[tid].https_chain = chain_str


@transact
def acme_cert_issuance(session, tid):
    return db_acme_cert_issuance(session, tid)


class AcmeHandler(BaseHandler):
    check_roles='admin'

    @inlineCallbacks
    def post(self):
        accnt_key = yield AcmeAccntKeyRes.create_file(self.request.tid)

        regr_uri, tos_url = letsencrypt.register_account_key(Settings.acme_directory_url, accnt_key)

        yield AcmeAccntKeyRes.save_accnt_uri(self.request.tid, regr_uri)

        returnValue({'terms_of_service': tos_url})

    @inlineCallbacks
    def put(self):
        is_ready = yield can_perform_acme_run(self.request.tid)
        if not is_ready:
            raise errors.ForbiddenOperation()

        yield acme_cert_issuance(self.request.tid)


class AcmeChallengeHandler(BaseHandler):
    check_roles = 'unauthenticated'
    bypass_basic_auth = True

    def get(self, token):
        tmp_chall_dict = State.tenant_state[self.request.tid].acme_tmp_chall_dict
        if token in tmp_chall_dict:
            log.info('Responding to valid .well-known request [%d]', self.request.tid)
            return tmp_chall_dict[token].tok

        raise errors.ResourceNotFound
