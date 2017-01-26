from tempfile import NamedTemporaryFile
from datetime import datetime
from StringIO import StringIO

from twisted.internet import ssl

from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, load_privatekey, FILETYPE_PEM
from OpenSSL._util import lib as _lib, ffi as _ffi

from globaleaks.utils.utility import log

# TODO TODO TODO TODO
# Move dhparam load and generate off of temporary files.
# TODO TODO TODO TODO

def generate_dh_params():
    # TODO(nskelsey|evilaliv3) ensure chosen params and generation is reasonable
    # and not easily abused
    dh = _lib.DH_new()
    log.info("Starting DH params generation")
    s = datetime.now()
    _lib.DH_generate_parameters_ex(dh, 2048, 2L, _ffi.NULL)
    log.info('DH params generation took: %2f secs' % (datetime.now() - s).total_seconds())

    with NamedTemporaryFile() as f_dh:
        bio = _lib.BIO_new_file(f_dh.name, "w")
        _lib.PEM_write_bio_DHparams(bio, dh)
        _lib.BIO_free(bio)
        f_dh.flush()
        dh_params = f_dh.read()
    return dh_params


def load_dh_params():
    bio = _lib.BIO_new_file(dhfile, b"r")
    if bio == _ffi.NULL:
        _raise_current_error()
        bio = _ffi.gc(bio, _lib.BIO_free)

    dh = _lib.PEM_read_bio_DHparams(bio, _ffi.NULL, _ffi.NULL, _ffi.NULL)
    dh = _ffi.gc(dh, _lib.DH_free)
    _lib.SSL_CTX_set_tmp_dh(context, dh)


"""
def __generate_dh_params():
    dh = _lib.DH_new()
    try:
        _lib.DH_generate_parameters_ex(dh, 2048, 5L, _ffi.NULL)

        #str_buf = StringIO()
        #with open(str_buf, 'w') as f:
        # Want to use DHparams print and avoid tmp_files...
        _lib.DHparams_print_fp(f, dh)

    except Exception as e:
        pass
    finally:
        print('generation took:', (datetime.now() - s).total_seconds())

    der = str_buf.getvalue()
    return der


def __load_dh_params(dh_param_der):
    str_buf = StringIO(dh_param_der)

    with open(str_buf, 'r') as f:
        bio = _lib.BIO_new_file(f, b"r")

    if bio == _ffi.NULL:
        _raise_current_error()
        bio = _ffi.gc(bio, _lib.BIO_free)

    dh = _lib.PEM_read_bio_DHparams(bio, _ffi.NULL, _ffi.NULL, _ffi.NULL)
    dh = _ffi.gc(dh, _lib.DH_free)
    return dh
"""


class TLSContextFactory(ssl.ContextFactory):
    def __init__(self, priv_key, certificate, intermediate, dh, cipher_list):
        """
        @param priv_key: String representation of the private key
        @param certificate: String representation of the certificate
        @param intermediate: String representation of the intermediate file
        @param dh: String representation of the DH parameters
        @param cipher_list: The SSL cipher list selection to use
        """
        # as discussed on https://trac.torproject.org/projects/tor/ticket/11598
        # there is no way of enabling all TLS methods excluding SSL.
        # the problem lies in the fact that SSL.TLSv1_METHOD | SSL.TLSv1_1_METHOD | SSL.TLSv1_2_METHOD
        # is denied by OpenSSL.
        #
        # As spotted by nickm the only good solution right now is to enable SSL.SSLv23_METHOD then explicitly
        # use options: SSL_OP_NO_SSLv2 and SSL_OP_NO_SSLv3
        #
        # This trick make openssl consider valid all TLS methods.
        ctx = SSL.Context(SSL.SSLv23_METHOD)

        ctx.set_options(SSL.OP_CIPHER_SERVER_PREFERENCE |
                        SSL.OP_NO_SSLv2 |
                        SSL.OP_NO_SSLv3 |
                        SSL.OP_NO_COMPRESSION |
                        SSL.OP_NO_TICKET)

        ctx.set_mode(SSL.MODE_RELEASE_BUFFERS)

        x509 = load_certificate(FILETYPE_PEM, certificate)
        ctx.use_certificate(x509)

        if intermediate != '':
            x509 = load_certificate(FILETYPE_PEM, intermediate)
            ctx.add_extra_chain_cert(x509)

        priv_key = load_privatekey(FILETYPE_PEM, priv_key)
        ctx.use_privatekey(priv_key)

        ctx.set_cipher_list(cipher_list)

        with NamedTemporaryFile() as f_dh:
            f_dh.write(dh)
            f_dh.flush()
            ctx.load_tmp_dh(f_dh.name)

        ecdh = _lib.EC_KEY_new_by_curve_name(_lib.NID_X9_62_prime256v1)
        ecdh = _ffi.gc(ecdh, _lib.EC_KEY_free)
        _lib.SSL_CTX_set_tmp_ecdh(ctx._context, ecdh)

        self.context = ctx

    def getContext(self):
        """
        Return an SSL context.
        """
        return self.context
