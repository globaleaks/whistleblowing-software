import tempfile

from twisted.internet import ssl

from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, load_privatekey, FILETYPE_PEM
from OpenSSL._util import lib as _lib, ffi as _ffi


class TLSContextFactory(ssl.ContextFactory):
    def __init__(self, privateKey, certificate, intermediate, dh, cipherList):
        """
        @param privateKey: String representation of the private key
        @param certificate: String representation of the certificate
        @param intermediate: String representation of the intermediate file
        @param dh: String representation of the DH parameters
        @param cipherList: The SSL cipher list selection to use
        """
        self.privateKey = privateKey
        self.certificate = certificate
        self.intermediate = intermediate

        # as discussed on https://trac.torproject.org/projects/tor/ticket/11598
        # there is no way of enabling all TLS methods excluding SSL.
        # the problem lies in the fact that SSL.TLSv1_METHOD | SSL.TLSv1_1_METHOD | SSL.TLSv1_2_METHOD
        # is denied by OpenSSL.
        #
        # As spotted by nickm the only good solution right now is to enable SSL.SSLv23_METHOD then explicitly
        # use options: SSL_OP_NO_SSLv2 and SSL_OP_NO_SSLv3
        #
        # This trick make openssl consider valid all TLS methods.
        self.sslmethod = SSL.SSLv23_METHOD

        self.dh = dh
        self.cipherList = cipherList

        self._ctx = SSL.Context(self.sslmethod)

        self._ctx.set_options(SSL.OP_CIPHER_SERVER_PREFERENCE |
                              SSL.OP_NO_SSLv2 |
                              SSL.OP_NO_SSLv3 |
                              SSL.OP_NO_COMPRESSION |
                              SSL.OP_NO_TICKET)

        self._ctx.set_mode(SSL.MODE_RELEASE_BUFFERS)

        x509 = load_certificate(FILETYPE_PEM, self.certificate)
        self._ctx.use_certificate(x509)

        if self.intermediate != '':
            x509 = load_certificate(FILETYPE_PEM, self.intermediate)
            self._ctx.add_extra_chain_cert(x509)

        pkey = load_privatekey(FILETYPE_PEM, self.privateKey)
        self._ctx.use_privatekey(pkey)

        self._ctx.set_cipher_list(self.cipherList)

        temp = tempfile.NamedTemporaryFile()
        temp.write(self.dh)
        temp.flush()
        self._ctx.load_tmp_dh(temp.name)
        temp.close()

        ecdh = _lib.EC_KEY_new_by_curve_name(_lib.NID_X9_62_prime256v1)
        ecdh = _ffi.gc(ecdh, _lib.EC_KEY_free)
        _lib.SSL_CTX_set_tmp_ecdh(self._ctx._context, ecdh)

        self._context = self._ctx

    def getContext(self):
        """
        Return an SSL context.
        """
        return self._ctx
