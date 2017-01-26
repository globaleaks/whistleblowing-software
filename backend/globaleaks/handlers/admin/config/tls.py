from datetime import datetime

from OpenSSL import crypto, SSL
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import PrivateFactory
from globaleaks.rest import requests
from globaleaks.rest import errors
from globaleaks.utils.utility import log
from globaleaks.utils.ssl import generate_dh_params
from globaleaks.utils import tls_master
from globaleaks.utils.utility import datetime_to_ISO8601


class FileResource(object):
    '''
    An interface for interacting with files stored on disk or in the db
    '''

    @staticmethod
    @transact
    def create_file(store, request):
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


class PrivKeyFileRes(FileResource):
    @staticmethod
    @transact
    def create_file(store, _):
        prv_fact = PrivateFactory(store)

        prv_https_key_pem = prv_fact.get_val('https_priv_key')

        # TODO move check
        if prv_https_key_pem != '':
            raise Exception("An https private key already exists")

        dh_params = prv_fact.get_val('https_dh_params')

        if dh_params == u'':
            log.info("Generating https_dh_params")
            dh_params = generate_dh_params()
            prv_fact.set_val('https_dh_parms')
            log.info("DH param generated and stored")

        log.info("Generating a new TLS key")
        prv_key = gen_RSA_key()
        pem_prv_key = crypto.dump_privatekey(SSL.FILETYPE_PEM, prv_key)
        prv_fact.set_val('https_priv_key', pem_prv_key)
        log.info("Finished key generation and storage")

    @staticmethod
    @transact
    def delete_file(store):
        prv_fact = PrivateFactory(store)
        # TODO(nskelsey) wipe key in a safer fashion or blame naif if it
        # all goes wrong.
        prv_fact.set_val('https_priv_key', u'')

    @staticmethod
    def db_serialize(store):
        k = PrivateFactory(store).get_val('https_priv_key')
        is_key_set = k != u''
        # TODO(nskelsey) this needs to be better
        return {'set': is_key_set}


class ChainFileRes(FileResource):
    @staticmethod
    @transact
    def create_file(store, json):
        prv_fact = PrivateFactory(store)
        log.info('Saw the following: %s' % json)
        # TODO Validate chain file
        prv_fact.set_val('https_chain', json['content'])

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
        ret = {
            'name': 'chain',
            'expiration_date': datetime_to_ISO8601(datetime.now()),
            'content': c,
            'set': c != u'',
        }
        return ret


class CertFileRes(FileResource):
    @staticmethod
    @transact
    def create_file(store, json):
        prv_fact = PrivateFactory(store)
        # TODO Validate cert
        prv_fact.set_val('https_cert', json['content'])

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
        ret = {
            'name': 'cert',
            'expiration_date': datetime_to_ISO8601(datetime.now()),
            'content': c,
            'set': c != u'',
        }
        return ret


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
        # TODO assert file exists
        file_res_cls = self.get_file_res_or_raise(name)
        yield file_res_cls.delete_file()

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, name):
        # TODO privKeyFileRes gets caught here because generate has no use for
        # the content = unicode json.
        req = self.validate_message(self.request.body,
                                    requests.AdminTLSCfgFileResourceDesc)

        file_res_cls = self.get_file_res_or_raise(name)

        # TODO assert file does not exist
        yield file_res_cls.create_file(req)
        self.set_status(201, 'Wrote everything')

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

    # TODO this loop is a bit of a mess.
    for key, file_res_cls in FileHandler.mapped_file_resources.iteritems():
        file_summaries[key] = file_res_cls.db_serialize(store)

    ret = {
      'enabled': prv_fact.get_val('https_enabled'),
      'runinng': True, # TODO process_sup.running
      'status_msg': GLSettings.state.process_supervisor.get_status(),
      'timestamp': datetime_to_ISO8601(datetime.now()),
      'files': file_summaries,
    }
    return ret


@transact
def try_to_enable_https(store):
    prv_fact = PrivateFactory(store)
    prv_fact.set_val('https_enabled', True)
    GLSettings.state.process_supervisor.db_maybe_launch_https_workers(store)


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
    prv_fact.set_val('https_dh_params', '')
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

    def post(self):
        '''
        This post 'enables' the tls config.
        '''
        # TODO(nskelsey) rate limit me
        yield try_to_enable_https()
        self.set_status(200)

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


def gen_x509_csr(key_pair, csr_fields):
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
    req = crypto.X509Req()
    subj = req.get_subject()

    for field, value in csr_fields.iteritems():
        setattr(subj, field, value)

    req.set_pubkey(key_pair)
    req.sign(key_pair, 'sha512')

    return req


@transact
def csr_gen(store, csr_fields):
    try:
        csr = gen_x509_csr(csr_fields)
        pem_csr = crypto.dump_certificate_request(SSL.FILETYPE_PEM, csr)
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
                'C':  request['country'],
                'ST': request['province'],
                'L':  request['city'],
                'O':  request['company'],
                'CN': request['commonname'],
                'emailAddress': request['email'],
        }

        if 'department' in request:
            csr_fields['OU'] = request['department']

        try:
          csr = yield csr_gen(csr_fields)
          self.write({'csr_txt': csr})
        except Exception as e:
          log.err(e)
          raise e

        self.set_status(200)
