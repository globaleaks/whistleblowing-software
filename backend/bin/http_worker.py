#!/usr/bin/env python

import json
import multiprocessing
import os
import signal
import socket
import tempfile

from sys import argv, executable

from twisted.internet import reactor, ssl, task
from twisted.protocols import tls
from twisted.python.compat import urllib_parse, urlquote
from twisted.web import proxy, resource, server

from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, load_privatekey, FILETYPE_PEM
from OpenSSL._util import lib as _lib, ffi as _ffi


def testFileAccess(f):
  return os.path.exists(f) and os.path.isfile(f) and os.access(f, os.R_OK)


def listenTCPonExistingFD(reactor, fd, factory):
    return reactor.adoptStreamPort(fd, socket.AF_INET, factory)


def listenSSLonExistingFD(reactor, fd, factory, contextFactory):
    tlsFactory = tls.TLSMemoryBIOFactory(contextFactory, False, factory)
    port = reactor.listenTCPonExistingFD(reactor, fd, tlsFactory)
    port._type = 'TLS'
    return port


class ServerContextFactory(ssl.ContextFactory):
    _context = None

    def __init__(self, privateKey, certificate, intermediate, dh, cipherList):
        """
        @param privateKeyFileName: Name of a file containing a private key
        @param certificateChainFileName: Name of a file containing a certificate chain
        @param dhFileName: Name of a file containing diffie hellman parameters
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

        # Create a context object right now.  This is to force validation of
        # the given parameters so that errors are detected earlier rather
        # than later.
        self.cacheContext()

    def cacheContext(self):
        if self._context is None:
            ctx = SSL.Context(self.sslmethod)

            ctx.set_options(SSL.OP_CIPHER_SERVER_PREFERENCE |
                            SSL.OP_NO_SSLv2 |
                            SSL.OP_NO_SSLv3 |
                            SSL.OP_NO_COMPRESSION |
                            SSL.OP_NO_TICKET)

            ctx.set_mode(SSL.MODE_RELEASE_BUFFERS)

            x509 = load_certificate(FILETYPE_PEM, self.certificate)
            ctx.use_certificate(x509)

            if self.intermediate != '':
                x509 = load_certificate(FILETYPE_PEM, self.intermediate)
                ctx.add_extra_chain_cert(x509)

            pkey = load_privatekey(FILETYPE_PEM, self.privateKey)
            ctx.use_privatekey(pkey)

            ctx.set_cipher_list(self.cipherList)

            temp = tempfile.NamedTemporaryFile()
            temp.write(self.dh)
            temp.flush()
            ctx.load_tmp_dh(temp.name)
            temp.close()

            ecdh = _lib.EC_KEY_new_by_curve_name(_lib.NID_X9_62_prime256v1)
            ecdh = _ffi.gc(ecdh, _lib.EC_KEY_free)
            _lib.SSL_CTX_set_tmp_ecdh(ctx._context, ecdh)

            self._context = ctx

    def getContext(self):
        """
        Return an SSL context.
        """
        return self._context


reactor.listenTCPonExistingFD = listenTCPonExistingFD
reactor.listenSSLonExistingFD = listenSSLonExistingFD


class ReverseProxyGzipResource(proxy.ReverseProxyResource):
    def getChild(self, path, request):
        child = ReverseProxyGzipResource(
            self.host, self.port, self.path + b'/' + urlquote(path, safe=b"").encode('utf-8'),
            self.reactor)

        return resource.EncodingResourceWrapper(child, [server.GzipEncoderFactory()])


def SigQUIT(SIG, FRM):
    try:
        reactor.stop()
    except Exception:
        pass


signal.signal(signal.SIGUSR1, SigQUIT)
signal.signal(signal.SIGTERM, SigQUIT)
signal.signal(signal.SIGINT, SigQUIT)


resource = ReverseProxyGzipResource('127.0.0.1', 8082, '')

http_factory = server.Site(resource)

print "Waiting for piped config"
config = json.loads(os.fdopen(2, 'r').read())

print "Received Server config over socket!"
tls_factory = ServerContextFactory(config['ssl_key'],
                                   config['ssl_cert'],
                                   config['ssl_intermediate'],
                                   config['ssl_dh'],
                                   config['ssl_cipher_list'])

reactor.listenSSLonExistingFD(reactor,
                              fd=3,
                              factory=http_factory,
                              contextFactory=tls_factory)

print "Starting an HTTPS listener"
reactor.run()
