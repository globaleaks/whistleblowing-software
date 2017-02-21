# -*- coding: utf-8 -*-
from datetime import datetime
from functools import wraps

from OpenSSL import crypto, SSL
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from twisted.internet.defer import inlineCallbacks

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
    @transact
    def perform_file_action(store):
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


def https_disabled(f):
    @wraps(f)
    def wrapper(store, *args, **kwargs):
        on = PrivateFactory(store).get_val('https_enabled')
        if on:
            raise errors.FailedSanityCheck()
        return f(store, *args, **kwargs)

    return wrapper


class PrivKeyFileRes(FileResource):
    validator = tls.PrivKeyValidator

    @staticmethod
    def gen_dh_params_if_none(prv_fact):
         dh_params = prv_fact.get_val('https_dh_params')

         if dh_params == u'':
             log.info("Generating https dh params")
             dh_params = tls.generate_dh_params()
             prv_fact.set_val('https_dh_params', dh_params)
             log.info("DH param generated and stored")

    @classmethod
    @transact
    @https_disabled
    def create_file(store, cls, raw_key):
        db_cfg = load_tls_dict(store)
        db_cfg['ssl_key'] = raw_key

        prv_fact = PrivateFactory(store)
        pkv = cls.validator()
        ok, err = pkv.validate(db_cfg)
        if ok:
            PrivKeyFileRes.gen_dh_params_if_none(prv_fact)
            prv_fact.set_val('https_priv_key', raw_key)
            prv_fact.set_val('https_priv_gen', False)
        else:
            log.info('Key validation failed')
        return ok

    @staticmethod
    @transact
    @https_disabled
    def perform_file_action(store):
        prv_fact = PrivateFactory(store)
        PrivKeyFileRes.gen_dh_params_if_none(prv_fact)

        log.info("Generating a new TLS key")
        prv_key = tls.gen_RSA_key()
        pem_prv_key = crypto.dump_privatekey(SSL.FILETYPE_PEM, prv_key)
        prv_fact.set_val('https_priv_key', pem_prv_key)
        prv_fact.set_val('https_priv_gen', True)

        log.info("Finished key generation and storage")

    @staticmethod
    @transact
    @https_disabled
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        # TODO(nskelsey) wipe key in a safer fashion or blame naif if it
        # all goes wrong.
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
    @https_disabled
    def create_file(store, cls, raw_cert):
        prv_fact = PrivateFactory(store)

        db_cfg = load_tls_dict(store)
        db_cfg['ssl_cert'] = raw_cert

        cv = cls.validator()
        ok, err = cv.validate(db_cfg)
        if ok:
            prv_fact.set_val('https_cert', raw_cert)
        else:
            log.info("Cert validation failed")
        return ok

    @staticmethod
    @transact
    @https_disabled
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_cert', u'')

    @staticmethod
    @transact
    @https_disabled
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
    @https_disabled
    def create_file(store, cls, raw_chain):
        prv_fact = PrivateFactory(store)

        db_cfg = load_tls_dict(store)
        db_cfg['ssl_intermediate'] = raw_chain

        cv = cls.validator()
        ok, err = cv.validate(db_cfg)
        if ok:
            prv_fact.set_val('https_chain', raw_chain)
        else:
            log.info('Chain validation failed')
        return ok

    @staticmethod
    @transact
    @https_disabled
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_chain', u'')

    @staticmethod
    @transact
    @https_disabled
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
    @https_disabled
    def create_file(store, cls, raw_csr):
        prv_fact = PrivateFactory(store)

        prv_fact.set_val('https_csr', raw_csr)

        return True

    @staticmethod
    @transact
    @https_disabled
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        prv_fact.set_val('https_csr', u'')

    @staticmethod
    @transact
    @https_disabled
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
    @inlineCallbacks
    def delete(self, name):
        file_res_cls = self.get_file_res_or_raise(name)
        yield file_res_cls.delete_file()

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, name):
        req = self.validate_message(self.request.body,
                                    requests.AdminTLSCfgFileResourceDesc)

        file_res_cls = self.get_file_res_or_raise(name)

        ok = yield file_res_cls.create_file(req['content'])
        if ok:
            self.set_status(201, 'Wrote everything')
        else:
            raise errors.ValidationError()


    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self, name):
        file_res_cls = self.get_file_res_or_raise(name)

        yield file_res_cls.perform_file_action()
        self.set_status(201, 'Accepted changes')


    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
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
def try_to_enable_and_launch_https(store):
    prv_fact = PrivateFactory(store)

    cv = tls.ChainValidator()
    db_cfg = load_tls_dict(store)
    db_cfg['https_enabled'] = False

    ok, err = cv.validate(db_cfg)
    if ok:
        prv_fact.set_val('https_enabled', True)
        # TODO move process launch out of transact or resolve when launch succeeds
        GLSettings.state.process_supervisor.db_maybe_launch_https_workers(store)
    return ok


@transact
def disable_https(store):
    prv_fact = PrivateFactory(store)
    log.info('Disabling https on the node.')
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
    @inlineCallbacks
    def post(self):
        '''
        '''
        # TODO(nskelsey) rate limit me
        ok = yield try_to_enable_and_launch_https()
        if ok:
            self.set_status(200)
        else:
            self.set_status(406)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self):
        '''
        This post disables and deactivates TLS config and subprocesses.
        '''
        yield disable_https()
        GLSettings.state.process_supervisor.shutdown()
        self.set_status(200)


class CSRFileHandler(FileHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
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
    @https_disabled
    def perform_action(store, csr_fields):
        db_cfg = load_tls_dict(store)

        pkv = tls.PrivKeyValidator()
        ok, err = pkv.validate(db_cfg)
        if not ok or not err is None:
            raise err

        key_pair = db_cfg['ssl_key']
        try:
            csr_txt = tls.gen_x509_csr(key_pair, csr_fields)
            log.info("Generated a new CSR")
            return csr_txt
        except Exception as e:
            log.err(e)
            raise errors.ValidationError('CSR gen failed')
