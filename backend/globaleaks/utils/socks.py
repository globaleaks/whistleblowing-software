# -*- coding: utf-8 -*-
# Minimal SOCKS5 implementation
# The implementation supports:
# - Plaintexts connections
# - HTTPS connections
# - The implementation perform optimistic data connection
#   as supported by Tor spec: https://gitweb.torproject.org/torspec.git/tree/socks-extensions.txt
# - No authentication is implented as it is not required
#   in the context of GlobaLeaks
#
# code concept from https://github.com/habnabit/txsocksx

import struct

from six import text_type

from twisted.internet import defer, interfaces
from twisted.internet.protocol import Protocol
from twisted.protocols import tls
from twisted.protocols.policies import ProtocolWrapper, WrappingFactory
from twisted.python.failure import Failure
from twisted.web.client import Agent, BrowserLikePolicyForHTTPS
from twisted.web.iweb import IAgentEndpointFactory, IAgent, IPolicyForHTTPS
from zope.interface import implementer, directlyProvides, providedBy


class SOCKSError(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.code = value


class SOCKS5ClientProtocol(ProtocolWrapper):
    def __init__(self, factory, wrappedProtocol, connectedDeferred, host, port):
        ProtocolWrapper.__init__(self, factory, wrappedProtocol)
        self._connectedDeferred = connectedDeferred
        self._host = host
        self._port = port
        self._buf = b''
        self.state = 0

    def error(self, error):
        self.transport.abortConnection()
        self.transport = None

    def socks_state_0(self):
        # error state
        self.error(SOCKSError(0x00))
        return

    def socks_state_1(self):
        if len(self._buf) < 2:
            return

        if self._buf[:2] != b"\x05\x00":
            # Anonymous access denied
            self.error(Failure(SOCKSError(0x00)))
            return

        self._buf = self._buf[2:]

        self.state = 2
        getattr(self, 'socks_state_%s' % self.state)()

    def socks_state_2(self):
        if len(self._buf) < 2:
            return

        if self._buf[:2] != b"\x05\x00":
            self.error(Failure(SOCKSError(ord(self._buf[1]))))
            return

        self._buf = self._buf[2:]

        self.state = 3
        getattr(self, 'socks_state_%s' % self.state)()

    def socks_state_3(self):
        if len(self._buf) < 8:
            return

        self._buf = self._buf[8:]

        if len(self._buf):
            self.wrappedProtocol.dataReceived(self._buf)

        self._buf = b''

        self.state = 4

    def makeConnection(self, transport):
        directlyProvides(self, providedBy(transport))
        Protocol.makeConnection(self, transport)
        self.factory.registerProtocol(self)

        # We implement only Anonymous access
        self.transport.write(struct.pack("!BB", 5, len(b"\x00")) + b"\x00")

        self.transport.write(struct.pack("!BBBBB", 5, 1, 0, 3, len(self._host)) + self._host + struct.pack("!H", self._port))
        self.wrappedProtocol.makeConnection(self)

        try:
            self._connectedDeferred.callback(self.wrappedProtocol)
        except Exception:
            pass

        self.state = 1

    def dataReceived(self, data):
        if self.state != 4:
            self._buf = b''.join([self._buf, data])
            getattr(self, 'socks_state_%s' % self.state)()
        else:
            self.wrappedProtocol.dataReceived(data)


class SOCKS5ClientFactory(WrappingFactory):
    protocol = SOCKS5ClientProtocol
    proto = None
    canceled = False

    def __init__(self, host, port, wrappedFactory):
        self.host = host
        self.port = port
        self.deferred = defer.Deferred(self._cancel)
        WrappingFactory.__init__(self, wrappedFactory)

    def buildProtocol(self, addr):
        try:
            self.proto = self.wrappedFactory.buildProtocol(addr)
        except Exception:
            self.deferred.errback()
        else:
            return self.protocol(self, self.proto, self.deferred, self.host, self.port)

    def clientConnectionFailed(self, connector, reason):
        if not self.canceled:
           self.deferred.errback(reason)

    def clientConnectionLost(self, connector, reason):
        pass

    def unregisterProtocol(self, p):
        try:
            del self.protocols[p]
        except Exception:
            pass

    def _cancel(self, d):
        self.proto.sender.transport.abortConnection()
        self.canceled = True


@implementer(interfaces.IStreamClientEndpoint)
class SOCKS5ClientEndpoint(object):
    def __init__(self, host, port, proxyEndpoint):
        self.host = host
        self.port = port
        self.proxyEndpoint = proxyEndpoint

    def connect(self, protocolFactory):
        proxyFac = SOCKS5ClientFactory(self.host, self.port, protocolFactory)
        d = self.proxyEndpoint.connect(proxyFac)
        d.addCallback(lambda proto: proxyFac.deferred)
        return d


@implementer(interfaces.IStreamClientEndpoint)
class TLSWrapClientEndpoint(object):
    _wrapper = tls.TLSMemoryBIOFactory

    def __init__(self, contextFactory, wrappedEndpoint):
        self.contextFactory = contextFactory
        self.wrappedEndpoint = wrappedEndpoint

    def connect(self, fac):
        fac = self._wrapper(self.contextFactory, True, fac)
        return self.wrappedEndpoint.connect(fac).addCallback(self._unwrapProtocol)

    def _unwrapProtocol(self, proto):
        return proto.wrappedProtocol


_Agent = Agent


@implementer(IAgentEndpointFactory, IAgent)
class SOCKS5Agent(object):
    endpointFactory = SOCKS5ClientEndpoint
    _tlsWrapper = TLSWrapClientEndpoint

    def __init__(self, reactor, contextFactory=BrowserLikePolicyForHTTPS(),
                 connectTimeout=None, bindAddress=None, pool=None, proxyEndpoint=None, endpointArgs={}):
        if not IPolicyForHTTPS.providedBy(contextFactory):
            raise NotImplementedError(
                'contextFactory must implement IPolicyForHTTPS')
        self.proxyEndpoint = proxyEndpoint
        self.endpointArgs = endpointArgs
        self._policyForHTTPS = contextFactory
        self._wrappedAgent = _Agent.usingEndpointFactory(
            reactor, self, pool=pool)

    def request(self, *a, **kw):
        return self._wrappedAgent.request(*a, **kw)

    def _getEndpoint(self, scheme, host, port):
        endpoint = self.endpointFactory(host, port, self.proxyEndpoint, **self.endpointArgs)

        if scheme == b'https':
            tlsPolicy = self._policyForHTTPS.creatorForNetloc(host, port)
            endpoint = self._tlsWrapper(tlsPolicy, endpoint)

        return endpoint

    def endpointForURI(self, uri):
        return self._getEndpoint(uri.scheme, uri.host, uri.port)
