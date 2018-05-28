# -*- coding: utf-8 -*-

import re

from OpenSSL import crypto, SSL
from OpenSSL._util import lib as _lib, ffi as _ffi
from OpenSSL.crypto import load_certificate, load_privatekey, FILETYPE_PEM, TYPE_RSA, PKey, dump_certificate_request, \
    X509Req, _new_mem_buf, _bio_to_string
from six import text_type, binary_type
from twisted.internet import ssl


class ValidationException(Exception):
    pass


def load_dh_params_from_string(ctx, dh_params_string):
    bio = _new_mem_buf()

    _lib.BIO_write(bio, dh_params_string.encode('ascii'), len(dh_params_string.encode('ascii'))) # pylint: disable=no-member
    dh = _lib.PEM_read_bio_DHparams(bio, _ffi.NULL, _ffi.NULL, _ffi.NULL) # pylint: disable=no-member
    dh = _ffi.gc(dh, _lib.DH_free) # pylint: disable=no-member
    _lib.SSL_CTX_set_tmp_dh(ctx._context, dh) # pylint: disable=no-member


def gen_dh_params(bits):
    dh = _lib.DH_new() # pylint: disable=no-member
    _lib.DH_generate_parameters_ex(dh, bits, 2, _ffi.NULL) # pylint: disable=no-member

    bio = _new_mem_buf()
    _lib.PEM_write_bio_DHparams(bio, dh) # pylint: disable=no-member
    return _bio_to_string(bio)


def gen_rsa_key(bits):
    """
    Generate an RSA key and returns it in PEM format.
    :rtype: An RSA key as an `pyopenssl.OpenSSL.crypto.PKey`
    """
    key = PKey()
    key.generate_key(TYPE_RSA, bits)

    return crypto.dump_privatekey(SSL.FILETYPE_PEM, key)


def gen_x509_csr_pem(key_pair, csr_fields, csr_sign_bits):
    req = gen_x509_csr(key_pair, csr_fields, csr_sign_bits)
    pem_csr = dump_certificate_request(SSL.FILETYPE_PEM, req)
    return pem_csr


def gen_x509_csr(key_pair, csr_fields, csr_sign_bits):
    """
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
    """
    req = X509Req()
    subj = req.get_subject()

    for field, value in csr_fields.items():
        setattr(subj, field, value)

    prv_key = load_privatekey(SSL.FILETYPE_PEM, key_pair)

    req.set_pubkey(prv_key)
    req.sign(prv_key, 'sha'+str(csr_sign_bits))

    return req


def parse_issuer_name(x509):
    """Returns the issuer's name from a `OpenSSL.crypto.X509` cert"""
    name = x509.get_issuer()
    if name.O is not None:
        return name.organizationName
    elif name.OU is not None:
        return name.organizationalUnitName
    elif name.CN is not None:
        return name.commonName
    elif name.emailAddress is not None:
        return name.emailAddress
    else:
        return ''


def split_pem_chain(s):
    """Splits an ascii armored cert chain into a list of strings which could be valid certs"""
    gex_str = r"-----BEGIN CERTIFICATE-----\r?.+?\r?-----END CERTIFICATE-----\r?\n?"
    gex = re.compile(gex_str, re.DOTALL)

    try:
        if isinstance(s, binary_type):
            s = text_type(s, 'utf-8')
        return [m.group(0) for m in gex.finditer(s)]
    except UnicodeDecodeError:
        return None

def new_tls_client_context():
    # evilaliv3:
    # As discussed on https://trac.torproject.org/projects/tor/ticket/11598
    # there is no way to enable all TLS methods excluding SSL.
    # the problem lies in the fact that SSL.TLSv1_METHOD | SSL.TLSv1_1_METHOD | SSL.TLSv1_2_METHOD
    # is denied by OpenSSL.
    #
    # As spotted by nickm the only good solution right now is to enable SSL.SSLv23_METHOD then explicitly
    # use options: SSL_OP_NO_SSLv2 and SSL_OP_NO_SSLv3
    #
    # This trick make openssl consider valid all TLS methods.
    ctx = SSL.Context(SSL.SSLv23_METHOD)

    ctx.set_options(SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3)

    return ctx


def new_tls_server_context():
    ctx = new_tls_client_context()

    ctx.set_options(SSL.OP_NO_COMPRESSION |
                    SSL.OP_NO_TICKET |
                    SSL.OP_CIPHER_SERVER_PREFERENCE)

    ctx.set_mode(SSL.MODE_RELEASE_BUFFERS)

    cipher_list = b'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-AES128-SHA'
    ctx.set_cipher_list(cipher_list)

    return ctx


class TLSClientContextFactory(ssl.ClientContextFactory):
    def getContext(self):
        return new_tls_client_context()


class TLSServerContextFactory(ssl.ContextFactory):
    def __init__(self, priv_key, certificate, intermediate, dh):
        """
        @param priv_key: String representation of the private key
        @param certificate: String representation of the certificate
        @param intermediate: String representation of the intermediate file
        @param dh: String representation of the DH parameters
        """
        self.ctx = new_tls_server_context()

        x509 = load_certificate(FILETYPE_PEM, certificate)
        self.ctx.use_certificate(x509)

        if intermediate:
            x509 = load_certificate(FILETYPE_PEM, intermediate)
            self.ctx.add_extra_chain_cert(x509)

        priv_key = load_privatekey(FILETYPE_PEM, priv_key)
        self.ctx.use_privatekey(priv_key)

        load_dh_params_from_string(self.ctx, dh)

        ecdh = _lib.EC_KEY_new_by_curve_name(_lib.NID_X9_62_prime256v1) # pylint: disable=no-member
        ecdh = _ffi.gc(ecdh, _lib.EC_KEY_free) # pylint: disable=no-member
        _lib.SSL_CTX_set_tmp_ecdh(self.ctx._context, ecdh) # pylint: disable=no-member

    def getContext(self):
        return self.ctx


class CtxValidator(object):
    parents = []

    def _validate_parents(self, cfg, ctx, check_expiration):
        for parent in self.parents:
            p_v = parent()
            p_v._validate(cfg, ctx, check_expiration)

    def _validate(self, cfg, ctx, check_expiration):
        raise NotImplementedError()

    def validate(self, cfg, must_be_disabled=True, check_expiration=True):
        """
        Checks the validity of the passed config for usage in an OpenSSLContext

        :param cfg: A `dict` composed of SSL material
        :param must_be_disabled: A flag to toggle checking of https_enabled
        :param check_expiration: A flag to toggle certificate expiration checks

        :rtype: A tuple of (Bool, Exception) where True, None signifies success

        """
        if must_be_disabled and cfg['https_enabled']:
            raise ValidationException('HTTPS must not be enabled')

        ctx = new_tls_server_context()
        try:
            self._validate_parents(cfg, ctx, check_expiration)
            self._validate(cfg, ctx, check_expiration)
        except Exception as err:
            return False, err
        return True, None


class PrivKeyValidator(CtxValidator):
    parents = []

    def _validate(self, cfg, ctx, check_expiration):
        raw_str = cfg['ssl_key']
        if not raw_str:
            raise ValidationException('No private key is set')

        # Note that the empty string here prevents valid PKCS8 encrypted
        # keys from being used instead of plain pem keys.
        priv_key = load_privatekey(FILETYPE_PEM, raw_str, passphrase=b"")

        if priv_key.type() != TYPE_RSA or not priv_key.check():
            raise ValidationException('Invalid RSA key')


class CertValidator(CtxValidator):
    parents = [PrivKeyValidator]

    def _validate(self, cfg, ctx, check_expiration):
        certificate = cfg['ssl_cert']
        if not certificate:
            raise ValidationException('There is no certificate')

        possible_chain = split_pem_chain(certificate)
        if len(possible_chain) < 1:
            raise ValidationException('The certificate is not in the right format.')

        if len(possible_chain) > 1:
            raise ValidationException('There is more than one certificate loaded.')

        x509 = load_certificate(FILETYPE_PEM, certificate)

        if check_expiration and x509.has_expired():
            raise ValidationException('The certficate has expired')

        ctx.use_certificate(x509)

        priv_key = load_privatekey(FILETYPE_PEM, cfg['ssl_key'], passphrase=b'')

        ctx.use_privatekey(priv_key)

        # With the certificate loaded check if the key matches
        ctx.check_privatekey()


class ChainValidator(CtxValidator):
    parents = [PrivKeyValidator, CertValidator]

    def _validate(self, cfg, ctx, check_expiration):
        store = ctx.get_cert_store()

        raw_chain = cfg['ssl_intermediate']
        chain = split_pem_chain(raw_chain)

        if not chain and raw_chain:
            raise ValidationException('The certificate chain is invalid')

        for cert in chain:
            x509 = load_certificate(FILETYPE_PEM, cert)

            if check_expiration and x509.has_expired():
                raise ValidationException('An intermediate certificate has expired')

            store.add_cert(x509)

        if not cfg['hostname']:
            raise ValidationException('No hostname set')
