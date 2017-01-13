from OpenSSL import crypto, SSL
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import PrivateFactory
from globaleaks.rest import requests
from globaleaks.rest import errors
from globaleaks.utils.utility import log
from . import http_master


def check_https(priv_key, cert, chain):
    if (priv_key == 'throw'):
        raise errors.InvalidInputFormat('Dummy exception raised')
    return True


@transact
def configure_https(store, request):
    # TODO validate config params with SSL logic
    priv_key, cert, chain = request['priv_key'], request['cert'], request['chain']
    
    privFact = PrivateFactory(store)

    privFact.set_val('https_priv_key', priv_key)
    privFact.set_val('https_cert', cert)
    privFact.set_val('https_chain', chain)

    if check_https(pk, cert, chain):
        http_master.launch_workers({}, priv_key, cert, chain, 'dhparam')
    else:
        raise errors.InternalServerError("Cert upload failed!")


def stop_serving_https():
    pass


@transact
def delete_https_config(store):
    privFact = PrivateFactory(store)
    log.info('Deleting all HTTPS configuration')

    privFact.set_val('https_priv_key', u'')
    privFact.set_val('https_cert', u'')
    privFact.set_val('https_chain', u'')


class CertFileHandler(BaseHandler):

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        req = self.validate_message(self.request.body,
                                    requests.AdminTLSCertFilesConfigDesc)

        try:
          yield configure_https(req)
        except Exception as e:
          log.err(e)
          self.set_status(400)
          return

        self.set_status(200)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self):
        try:
          yield delete_tls()
        except Exception as e:
          log.err(e)
          self.set_status(400)
          return

        self.set_status(200)

class ConfigHandler(BaseHandler):

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def get(self):
        https_cfg = {
            'state': 'empty',
            'cert': 'py-back',
            'priv_key': '',
            'chain': '',
        }
        self.write(https_cfg)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self):
        yield stop_serving_https()
        yield delete_https_config()
        self.set_status(200)


def gen_RSA_key():
    '''
    gen_x509_key uses the default settings to generate the key params.
    TODO evaluate how defaults are selected...........................

    :rtype: An RSA key as an `pyopenssl.OpenSSL.crypto.PKey`
    '''
    pub_key = crypto.PKey()
    #TODO(@evilaliv3|@nskelsey) pick real params
    pub_key.generate_key(crypto.TYPE_RSA, 1024)

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
def key_and_csr_gen(store, csr_fields):
    '''
    key_and_csr_gen oversees the generation of an X.509 key and a corresponding
    CSR for that key. If the key already exists, only the CSR is generated. If
    there are any errors, the generated key is deleted, the CSR is ignored, and
    the function returns with a non descript error code.
    '''
    try:
        prv_fact = PrivateFactory(store)

        prv_https_key_pem = prv_fact.get_val('https_priv_key')

        if prv_https_key_pem != '':
            raise Exception("An https private key already exists")

        log.info("Generating a new key")
        prv_key = gen_RSA_key()
        pem_prv_key = crypto.dump_privatekey(SSL.FILETYPE_PEM, prv_key)
        prv_fact.set_val('https_priv_key', pem_prv_key)
        log.info("Finished key generation and storage")

        csr = gen_x509_csr(prv_key, csr_fields)
        pem_csr = crypto.dump_certificate_request(SSL.FILETYPE_PEM, csr)
        log.info("Generated a new CSR")

        return pem_csr
    except Exception as e:
        log.err(e)
        raise errors.InternalServerError('Key gen failed')


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
          csr = yield key_and_csr_gen(csr_fields)
          self.write({'csr_txt': csr})
        except Exception as e:
          log.err(e)
          raise e

        self.set_status(200)
