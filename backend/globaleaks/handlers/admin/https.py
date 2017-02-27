# -*- coding: utf-8 -*-
from datetime import datetime
from functools import wraps

from OpenSSL import crypto, SSL
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import PrivateFactory, NodeFactory, load_tls_dict
from globaleaks.rest import errors, requests
from globaleaks.utils import tls
from globaleaks.utils.utility import datetime_to_ISO8601, format_cert_expr_date, log


class FileResource(object):
    '''
    An interface for interacting with files stored on disk or in the db
    '''
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
        '''
        :rtype: A `unicode` string
        '''
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
        '''
        :rtype: A `dict` to be converted into JSON for delivery to a client
        '''
        raise errors.MethodNotImplemented()

    @classmethod
    @transact
    def should_gen_dh_params(store, cls):
        return PrivateFactory(store).get_val('https_dh_params') == u''

    @staticmethod
    @transact
    def save_dh_params(store, dh_params):
        PrivateFactory(store).set_val('https_dh_params', dh_params)

    @classmethod
    @inlineCallbacks
    def generate_dh_params_if_missing(cls):
        gen_dh = yield cls.should_gen_dh_params()
        if gen_dh:
            log.debug("Generating the HTTPS DH params")
            dh_params = yield deferToThread(tls.gen_dh_params, GLSettings.key_bits)

            log.debug("Storing the HTTPS DH params")
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
        ok, err = pkv.validate(db_cfg)
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
        log.debug("Generating the HTTPS key")
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
        ok, err = cv.validate(db_cfg)
        if ok:
            prv_fact.set_val('https_cert', raw_cert)
        else:
            log.err("Cert validation failed")
        return ok

    @staticmethod
    @transact
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_cert', u'')

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
            'issuer': x509.get_issuer().organizationName,
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
        ok, err = cv.validate(db_cfg)
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
            'issuer': x509.get_issuer().organizationName,
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
    mapped_file_resources = {
        'priv_key': PrivKeyFileRes,
        'cert':  CertFileRes,
        'chain': ChainFileRes,
        'csr': CsrFileRes,
    }

    def get_file_res_or_raise(self, name):
        if name not in self.mapped_file_resources:
            raise errors.MethodNotImplemented()
        else:
            return self.mapped_file_resources[name]

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @BaseHandler.https_disabled
    @inlineCallbacks
    def delete(self, name):
        file_res_cls = self.get_file_res_or_raise(name)
        yield file_res_cls.delete_file()

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self, name):
        req = self.validate_message(self.request.body,
                                    requests.AdminTLSCfgFileResourceDesc)

        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.generate_dh_params_if_missing()

        ok = yield file_res_cls.create_file(req['content'])
        if ok:
            self.set_status(201, 'Wrote everything')
        else:
            raise errors.ValidationError()

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @BaseHandler.https_disabled
    @inlineCallbacks
    def put(self, name):
        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.generate_dh_params_if_missing()

        yield file_res_cls.perform_file_action()

        self.set_status(201, 'Accepted changes')

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @BaseHandler.https_disabled
    @inlineCallbacks
    def get(self, name):
        file_res_cls = self.get_file_res_or_raise(name)

        file_blob = yield file_res_cls.get_file()

        self.write(file_blob)


@transact
def serialize_https_config_summary(store):
    prv_fact = PrivateFactory(store)

    file_summaries = {}

    for key, file_res_cls in FileHandler.mapped_file_resources.iteritems():
        file_summaries[key] = file_res_cls.db_serialize(store)

    ret = {
      'enabled': prv_fact.get_val('https_enabled'),
      'running': GLSettings.state.process_supervisor.is_running(),
      'status': GLSettings.state.process_supervisor.get_status(),
      'files': file_summaries,
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
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        https_cfg = yield serialize_https_config_summary()
        self.write(https_cfg)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self):
        try:
            yield try_to_enable_https()
            yield GLSettings.state.process_supervisor.maybe_launch_https_workers()
            self.set_status(200)
        except Exception as e:
            log.err(e)
            self.set_status(406)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @BaseHandler.https_enabled
    @inlineCallbacks
    def put(self):
        '''
        Disables HTTPS config and shutdown subprocesses.
        '''
        yield disable_https()
        GLSettings.memory_copy.private.https_enabled = False
        yield GLSettings.state.process_supervisor.shutdown()
        self.set_status(200)


class CSRFileHandler(FileHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @BaseHandler.https_disabled
    @inlineCallbacks
    def post(self, name):
        request = self.validate_message(self.request.body,
                                        requests.AdminCSRFileDesc)

        desc = request['content']

        csr_fields = {
                'C':  desc['country'].upper(),
                'ST': desc['province'],
                'L':  desc['city'],
                'O':  desc['company'],
                'OU': desc['department'],
                'CN': desc['commonname'],
                'emailAddress': desc['email'],
        }

        csr_txt = yield self.perform_action(csr_fields)

        file_res_cls = self.get_file_res_or_raise(name)

        ok = yield file_res_cls.create_file(csr_txt)
        if ok:
            self.set_status(201, 'Wrote everything')
        else:
            raise errors.ValidationError()

        self.set_status(200)

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
            csr_txt = tls.gen_x509_csr(key_pair, csr_fields, GLSettings.csr_sign_bits)
            log.debug("Generated a new CSR")
            return csr_txt
        except Exception as e:
            log.err(e)
            raise errors.ValidationError('CSR gen failed')
