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
from globaleaks.rest import requests
from globaleaks.rest import errors
from globaleaks.utils.utility import log
from globaleaks.utils import tls
from globaleaks.utils import tls_master
from globaleaks.utils.utility import datetime_to_ISO8601, format_cert_expr_date


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


def gen_dh_params_if_none(prv_fact):
    dh_params = prv_fact.get_val('https_dh_params')

    if dh_params == u'':
        log.info("Generating https dh params")
        dh_params = tls.generate_dh_params()
        prv_fact.set_val('https_dh_params', dh_params)
        log.info("DH param generated and stored")


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

    @classmethod
    @transact
    def create_file(store, cls, raw_key):
        db_cfg = load_tls_dict(store)
        db_cfg['key'] = raw_key

        prv_fact = PrivateFactory(store)
        pkv = cls.validator()
        ok, err = pkv.validate(db_cfg)
        if ok:
            gen_dh_params_if_none(prv_fact)
            prv_fact.set_val('https_priv_key', raw_key)
        else:
            log.info('Key validation failed')
        return ok

    @staticmethod
    @transact
    @https_disabled
    def perform_file_action(store):
        prv_fact = PrivateFactory(store)
        gen_dh_params_if_none(prv_fact)

        log.info("Generating a new TLS key")

        prv_key = gen_RSA_key()
        pem_prv_key = crypto.dump_privatekey(SSL.FILETYPE_PEM, prv_key)
        prv_fact.set_val('https_priv_key', pem_prv_key)

        log.info("Finished key generation and storage")

    @staticmethod
    @transact
    @https_disabled
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        # TODO(nskelsey) wipe key in a safer fashion or blame naif if it
        # all goes wrong.
        prv_fact.set_val('https_priv_key', u'')

    @staticmethod
    def db_serialize(store):
        k = PrivateFactory(store).get_val('https_priv_key')
        is_key_set = k != u''

        return {
            'set': is_key_set,
        }


class CertFileRes(FileResource):
    validator = tls.CertValidator

    @classmethod
    @transact
    def create_file(store, cls, raw_cert):
        prv_fact = PrivateFactory(store)

        db_cfg = load_tls_dict(store)
        db_cfg['cert'] = raw_cert

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
        if c == u'':
            return {'name': 'chain', 'set': False}

        x509 = load_certificate(FILETYPE_PEM, c)
        expr_date = format_cert_expr_date(x509.get_notAfter())

        return {
            'name': 'chain',
            'issuer': x509.get_issuer().organizationName,
            'expiration_date': datetime_to_ISO8601(expr_date),
            'set': True,
        }


class FileHandler(BaseHandler):
    mapped_file_resources = {
        'priv_key': PrivKeyFileRes,
        'cert':  CertFileRes,
        'chain': ChainFileRes,
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

    url = NodeFactory(store).get_val('public_site')

    ret = {
      'https_url': url,
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
        # TODO move process launch out of transact or resolve when launch succeeds
        GLSettings.state.process_supervisor.db_maybe_launch_https_workers(store)
    return ok


@transact
def try_to_disable_https(store):
    prv_fact = PrivateFactory(store)
    log.info('Disabling https on the node.')
    prv_fact.set_val('https_enabled', False)
    GLSettings.state.process_supervisor.shutdown()


@transact
def delete_https_config(store):
    prv_fact = PrivateFactory(store)
    log.info('Deleting all HTTPS configuration')

    prv_fact.set_val('https_priv_key', '')
    prv_fact.set_val('https_cert', '')
    prv_fact.set_val('https_chain', '')
    #prv_fact.set_val('https_dh_params', '')
    prv_fact.set_val('https_enabled', False)
    GLSettings.state.process_supervisor.shutdown()


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
    def delete(self):
        yield delete_https_config()
        self.set_status(200)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        '''
        This post 'enables' the tls config.
        '''
        # TODO(nskelsey) rate limit me
        ok = yield try_to_enable_https()
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
        # TODO(nskelsey) rate limit me
        yield try_to_disable_https()
        self.set_status(200)


def gen_RSA_key():
    '''
    gen_x509_key uses the default settings to generate the key params.
    TODO evaluate how defaults are selected...........................

    :rtype: An RSA key as an `pyopenssl.OpenSSL.crypto.PKey`
    '''
    pub_key = crypto.PKey()
    #TODO TODO TODO TODO TODO TODO TODO TODO TODO
    #TODO(evilaliv3|nskelsey) pick real params
    #TODO TODO TODO TODO TODO TODO TODO TODO TODO
    pub_key.generate_key(crypto.TYPE_RSA, 1024)
    #TODO TODO TODO TODO TODO TODO TODO TODO TODO
    #TODO TODO TODO TODO TODO TODO TODO TODO TODO

    return pub_key


@transact
def gen_x509_csr(store, csr_fields):
    '''
    gen_x509_csr creates a certificate signature request by applying the passed
    fields to the subject of the request, attaches the public key's fingerprint
    and signs the request using the private key.

    csr_fields dictionary and generates a
    certificate request using the passed keypair. Note that the default digest
    is sha256.

    :param key_pair: The key pair that will sign the request
    :type key_pair: :py:data:`OpenSSL.crypto.PKey` the key must have an attached
    private component.

    :param csr_fields: The certifcate issuer's details in X.509 Distinguished
    Name format.
    :type csr_fields: :py:data:`dict`
        C     - Country name
        ST    - State or province name
        L     - Locality name
        O     - Organization name
        OU    - Organizational unit name
        CN    - Common name
        emailAddress - E-mail address

    :rtype: A `pyopenssl.OpenSSL.crypto.X509Req`
    '''
    try:
        req = crypto.X509Req()
        subj = req.get_subject()

        for field, value in csr_fields.iteritems():
            setattr(subj, field, value)

        str_prv_key = PrivateFactory(store).get_val('https_priv_key')
        prv_key = crypto.load_privatekey(SSL.FILETYPE_PEM, str_prv_key)

        req.set_pubkey(prv_key)
        req.sign(prv_key, 'sha512')
        # TODO clean prv_key and str_prv_key from memory

        pem_csr = crypto.dump_certificate_request(SSL.FILETYPE_PEM, req)
        # TODO clean req from memory

        log.info("Generated a new CSR")
        return pem_csr
    except Exception as e:
        log.err(e)
        raise errors.InternalServerError('CSR gen failed')


class CSRConfigHandler(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.body,
                                        requests.AdminCSRConfigDesc)
        csr_fields = {
                'C':  request['country'].upper(),
                'ST': request['province'],
                'L':  request['city'],
                'O':  request['company'],
                'CN': request['commonname'],
                'emailAddress': request['email'],
        }

        if 'department' in request:
            csr_fields['OU'] = request['department']

        csr_txt = yield gen_x509_csr(csr_fields)

        self.set_status(200)
        self.write(csr_txt)
