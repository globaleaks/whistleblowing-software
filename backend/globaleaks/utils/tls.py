import os

from tempfile import NamedTemporaryFile
from datetime import datetime

from twisted.internet import ssl

from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, dump_certificate, load_privatekey, FILETYPE_PEM, TYPE_RSA, X509StoreContext
from OpenSSL._util import lib as _lib, ffi as _ffi


from pyasn1.type import univ, constraint, char, namedtype, tag
from pyasn1.codec.der.decoder import decode


class ValidationException(Exception):
    pass


def load_dh_params_from_string(ctx, dh_params_string):
    with NamedTemporaryFile() as temp:
        temp.write(dh_params_string)
        temp.flush()
        ctx.load_tmp_dh(temp.name)


def generate_dh_params():
    # TODO(nskelsey|evilaliv3) ensure chosen params and generation is reasonable
    # and not easily abused
    dh = _lib.DH_new()
    s = datetime.now()
    _lib.DH_generate_parameters_ex(dh, 2048, 2L, _ffi.NULL)

    # TODO TODO TODO TODO TODO TODO TODO TODO
    # Move dhparam load and generate off of temporary files.
    # TODO TODO TODO TODO TODO TODO TODO TODO
    with NamedTemporaryFile() as f_dh:
        bio = _lib.BIO_new_file(f_dh.name, "w")
        _lib.PEM_write_bio_DHparams(bio, dh)
        _lib.BIO_free(bio)
        f_dh.flush()
        dh_params = f_dh.read()
    # TODO TODO TODO TODO TODO TODO TODO TODO

    return dh_params


def new_tls_context():
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

    ctx.set_options(SSL.OP_NO_SSLv2 |
                    SSL.OP_NO_SSLv3 |
                    SSL.OP_NO_COMPRESSION |
                    SSL.OP_NO_TICKET |
                    SSL.OP_CIPHER_SERVER_PREFERENCE)

    ctx.set_mode(SSL.MODE_RELEASE_BUFFERS)

    cipher_list = bytes('ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-AES128-SHA')
    ctx.set_cipher_list(cipher_list)

    return ctx


class TLSServerContextFactory(ssl.ContextFactory):
    def __init__(self, priv_key, certificate, intermediate, dh):
        """
        @param priv_key: String representation of the private key
        @param certificate: String representation of the certificate
        @param intermediate: String representation of the intermediate file
        @param dh: String representation of the DH parameters
        """
        self.ctx = new_tls_context()

        x509 = load_certificate(FILETYPE_PEM, certificate)
        self.ctx.use_certificate(x509)

        if intermediate != '':
            x509 = load_certificate(FILETYPE_PEM, intermediate)
            self.ctx.add_extra_chain_cert(x509)

        priv_key = load_privatekey(FILETYPE_PEM, priv_key)
        self.ctx.use_privatekey(priv_key)

        load_dh_params_from_string(self.ctx, dh)

        ecdh = _lib.EC_KEY_new_by_curve_name(_lib.NID_X9_62_prime256v1)
        ecdh = _ffi.gc(ecdh, _lib.EC_KEY_free)
        _lib.SSL_CTX_set_tmp_ecdh(self.ctx._context, ecdh)

    def getContext(self):
        return self.ctx


class CtxValidator(object):
    parents = []

    def _validate_parents(self, cfg, ctx):
        for parent in self.parents:
            p_v = parent()
            p_v._validate(cfg, ctx)

    def _validate(self, cfg, ctx):
        raise NotImplementedError()

    def validate(self, cfg, must_be_disabled=True):
        if must_be_disabled and cfg['https_enabled']:
            raise ValidationException('HTTPS must not be enabled')

        ctx = new_tls_context()
        try:
            self._validate_parents(cfg, ctx)
            self._validate(cfg, ctx)
        except Exception as err:
            return (False, err)
        return (True, None)


class PrivKeyValidator(CtxValidator):
    parents = []

    def _validate(self, cfg, ctx):
        # Note that the empty string here prevents valid PKCS8 encrypted
        # keys from being used instead of plain pem keys.
        raw_str = cfg['key']
        if raw_str == u'':
            raise ValidationException('No private key is set')

        priv_key = load_privatekey(FILETYPE_PEM, raw_str, "")

        # TODO fix cffi dep for 14.04
        # if priv_key.type() == TYPE_RSA:
        #     ok = priv_key.check()
        #     if not ok:
        #         raise ValidationException('Invalid RSA key')


class CertValidator(CtxValidator):
    parents = [PrivKeyValidator]

    def _validate(self, cfg, ctx):
        certificate = cfg['cert']
        if certificate == u'':
            raise ValidationException('There is no certificate')

        x509 = load_certificate(FILETYPE_PEM, certificate)

        # NOTE when a cert expires it will fail validation.
        if x509.has_expired():
            raise ValidationException('The certficate has expired')

        ctx.use_certificate(x509)

        priv_key = load_privatekey(FILETYPE_PEM, cfg['key'], '')

        ctx.use_privatekey(priv_key)

        # With the certificate loaded check if the key matches
        ctx.check_privatekey()


class ChainValidator(CtxValidator):
    parents = [PrivKeyValidator, CertValidator]

    def _validate(self, cfg, ctx):
        store = ctx.get_cert_store()

        intermediate = cfg['ssl_intermediate']
        if intermediate != u'':
            x509 = load_certificate(FILETYPE_PEM, intermediate)

            if x509.has_expired():
                raise ValidationException('The intermediate cert has expired')

            store.add_cert(x509)

        for value in certificateAuthorityMap.values():
            store.add_cert(value)

        x509 = load_certificate(FILETYPE_PEM, cfg['cert'])
        X509StoreContext(store, x509).verify_certificate()


class ContextValidator(CtxValidator):
    parents = [PrivKeyValidator, CertValidator, ChainValidator]

    # TODO unused but ressurected :)

    def _validate(self, cfg, ctx):
        if cfg['ssl_dh'] == u'':
            raise ValidationException('There is not dh parameter set')

        with NamedTemporaryFile() as f_dh:
            f_dh.write(db_cfg['ssl_dh'])
            f_dh.flush()
            # TODO ensure load can deal with untrusted input
            ctx.load_tmp_dh(f_dh.name)

        ecdh = _lib.EC_KEY_new_by_curve_name(_lib.NID_X9_62_prime256v1)
        ecdh = _ffi.gc(ecdh, _lib.EC_KEY_free)
        _lib.SSL_CTX_set_tmp_ecdh(ctx._context, ecdh)


class GeneralName(univ.Choice):
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('dNSName', char.IA5String().subtype(
                implicitTag=tag.Tag(tag.tagClassContext, tag.tagFormatSimple, 2)
            )
        ),
    )

class GeneralNames(univ.SequenceOf):
    componentType = GeneralName()
    sizeSpec = univ.SequenceOf.sizeSpec + constraint.ValueSizeConstraint(1, 1024)


def altnames(cert):
    altnames = []

    for i in range(cert.get_extension_count()):
        ext = cert.get_extension(i)
        if ext.get_short_name() == "subjectAltName":
            dec = decode(ext.get_data(), asn1Spec=GeneralNames())
            for j in dec[0]:
                altnames.append(j[0].asOctets())

    return altnames


def should_redirect(glsettings, request):
    if (glsettings.memory_copy.private.https_enabled and \
        request.protocol == 'http' and \
        not request.host in glsettings.internal_hosts):
        return True
    else:
        return False
