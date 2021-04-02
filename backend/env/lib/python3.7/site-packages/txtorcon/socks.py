# in-progress; implementing SOCKS5 client-side stuff as extended by
# tor because txsocksx will not be getting Python3 support any time
# soon, and its underlying dependency (Parsely) also doesn't support
# Python3. Also, Tor's SOCKS5 implementation is especially simple,
# since it doesn't do BIND or UDP ASSOCIATE.

from __future__ import print_function

import six
import struct
from socket import inet_pton, inet_ntoa, inet_aton, AF_INET6, AF_INET

from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.address import IPv4Address, IPv6Address, HostnameAddress
from twisted.python.failure import Failure
from twisted.protocols import portforward
from twisted.protocols import tls
from twisted.internet.interfaces import IStreamClientEndpoint
from zope.interface import implementer
import ipaddress
import automat

from txtorcon import util


__all__ = (
    'resolve',
    'resolve_ptr',
    'SocksError',
    'GeneralServerFailureError',
    'ConnectionNotAllowedError',
    'NetworkUnreachableError',
    'HostUnreachableError',
    'ConnectionRefusedError',
    'TtlExpiredError',
    'CommandNotSupportedError',
    'AddressTypeNotSupportedError',
    'TorSocksEndpoint',
)


def _create_ip_address(host, port):
    if not isinstance(host, six.text_type):
        raise ValueError(
            "'host' must be {}, not {}".format(six.text_type, type(host))
        )
    try:
        a = ipaddress.ip_address(host)
    except ValueError:
        a = None
    if isinstance(a, ipaddress.IPv4Address):
        return IPv4Address('TCP', host, port)
    if isinstance(a, ipaddress.IPv6Address):
        return IPv6Address('TCP', host, port)
    addr = HostnameAddress(host, port)
    addr.host = host
    return addr


class _SocksMachine(object):
    """
    trying to prototype the SOCKS state-machine in automat

    This is a SOCKS state machine to make a single request.
    """

    _machine = automat.MethodicalMachine()
    SUCCEEDED = 0x00
    REPLY_IPV4 = 0x01
    REPLY_HOST = 0x03
    REPLY_IPV6 = 0x04

    # XXX address = (host, port) instead
    def __init__(self, req_type, host,
                 port=0,
                 on_disconnect=None,
                 on_data=None,
                 create_connection=None):
        if req_type not in self._dispatch:
            raise ValueError(
                "Unknown request type '{}'".format(req_type)
            )
        if req_type == 'CONNECT' and create_connection is None:
            raise ValueError(
                "create_connection function required for '{}'".format(
                    req_type
                )
            )
        if not isinstance(host, (bytes, str, six.text_type)):
            raise ValueError(
                "'host' must be text".format(type(host))
            )
        # XXX what if addr is None?
        self._req_type = req_type
        self._addr = _create_ip_address(six.text_type(host), port)
        self._data = b''
        self._on_disconnect = on_disconnect
        self._create_connection = create_connection
        # XXX FIXME do *one* of these:
        self._on_data = on_data
        self._outgoing_data = []
        # the other side of our proxy
        self._sender = None
        self._when_done = util.SingleObserver()

    def when_done(self):
        """
        Returns a Deferred that fires when we're done
        """
        return self._when_done.when_fired()

    def _data_to_send(self, data):
        if self._on_data:
            self._on_data(data)
        else:
            self._outgoing_data.append(data)

    def send_data(self, callback):
        """
        drain all pending data by calling `callback()` on it
        """
        # a "for x in self._outgoing_data" would potentially be more
        # efficient, but then there's no good way to bubble exceptions
        # from callback() out without lying about how much data we
        # processed .. or eat the exceptions in here.
        while len(self._outgoing_data):
            data = self._outgoing_data.pop(0)
            callback(data)

    def feed_data(self, data):
        # I feel like maybe i'm doing all this buffering-stuff
        # wrong. but I also don't want a bunch of "received 1 byte"
        # etc states hanging off everything that can "get data"
        self._data += data
        self.got_data()

    @_machine.output()
    def _parse_version_reply(self):
        "waiting for a version reply"
        if len(self._data) >= 2:
            reply = self._data[:2]
            self._data = self._data[2:]
            (version, method) = struct.unpack('BB', reply)
            if version == 5 and method in [0x00, 0x02]:
                self.version_reply(method)
            else:
                if version != 5:
                    self.version_error(SocksError(
                        "Expected version 5, got {}".format(version)))
                else:
                    self.version_error(SocksError(
                        "Wanted method 0 or 2, got {}".format(method)))

    def _parse_ipv4_reply(self):
        if len(self._data) >= 10:
            addr = inet_ntoa(self._data[4:8])
            port = struct.unpack('H', self._data[8:10])[0]
            self._data = self._data[10:]
            if self._req_type == 'CONNECT':
                self.reply_ipv4(addr, port)
            else:
                self.reply_domain_name(addr)

    def _parse_ipv6_reply(self):
        if len(self._data) >= 22:
            addr = self._data[4:20]
            port = struct.unpack('H', self._data[20:22])[0]
            self._data = self._data[22:]
            self.reply_ipv6(addr, port)

    def _parse_domain_name_reply(self):
        assert len(self._data) >= 8  # _parse_request_reply checks this
        addrlen = struct.unpack('B', self._data[4:5])[0]
        # may simply not have received enough data yet...
        if len(self._data) < (5 + addrlen + 2):
            return
        addr = self._data[5:5 + addrlen]
        # port = struct.unpack('H', self._data[5 + addrlen:5 + addrlen + 2])[0]
        self._data = self._data[5 + addrlen + 2:]
        self.reply_domain_name(addr)

    @_machine.output()
    def _parse_request_reply(self):
        "waiting for a reply to our request"
        # we need at least 6 bytes of data: 4 for the "header", such
        # as it is, and 2 more if it's DOMAINNAME (for the size) or 4
        # or 16 more if it's an IPv4/6 address reply. plus there's 2
        # bytes on the end for the bound port.
        if len(self._data) < 8:
            return
        msg = self._data[:4]

        # not changing self._data yet, in case we've not got
        # enough bytes so far.
        (version, reply, _, typ) = struct.unpack('BBBB', msg)

        if version != 5:
            self.reply_error(SocksError(
                "Expected version 5, got {}".format(version)))
            return

        if reply != self.SUCCEEDED:
            self.reply_error(_create_socks_error(reply))
            return

        reply_dispatcher = {
            self.REPLY_IPV4: self._parse_ipv4_reply,
            self.REPLY_HOST: self._parse_domain_name_reply,
            self.REPLY_IPV6: self._parse_ipv6_reply,
        }
        try:
            method = reply_dispatcher[typ]
        except KeyError:
            self.reply_error(SocksError(
                "Unexpected response type {}".format(typ)))
            return
        method()

    @_machine.output()
    def _make_connection(self, addr, port):
        "make our proxy connection"
        sender = self._create_connection(addr, port)
        # XXX look out! we're depending on this "sender" implementing
        # certain Twisted APIs, and the state-machine shouldn't depend
        # on that.

        # XXX also, if sender implements producer/consumer stuff, we
        # should register ourselves (and implement it to) -- but this
        # should really be taking place outside the state-machine in
        # "the I/O-doing" stuff
        self._sender = sender
        self._when_done.fire(sender)

    @_machine.output()
    def _domain_name_resolved(self, domain):
        self._when_done.fire(domain)

    @_machine.input()
    def connection(self):
        "begin the protocol (i.e. connection made)"

    @_machine.input()
    def disconnected(self, error):
        "the connection has gone away"

    @_machine.input()
    def got_data(self):
        "we recevied some data and buffered it"

    @_machine.input()
    def version_reply(self, auth_method):
        "the SOCKS server replied with a version"

    @_machine.input()
    def version_error(self, error):
        "the SOCKS server replied, but we don't understand"

    @_machine.input()
    def reply_error(self, error):
        "the SOCKS server replied with an error"

    @_machine.input()
    def reply_ipv4(self, addr, port):
        "the SOCKS server told me an IPv4 addr, port"

    @_machine.input()
    def reply_ipv6(self, addr, port):
        "the SOCKS server told me an IPv6 addr, port"

    @_machine.input()
    def reply_domain_name(self, domain):
        "the SOCKS server told me a domain-name"

    @_machine.input()
    def answer(self):
        "the SOCKS server replied with an answer"

    @_machine.output()
    def _send_version(self):
        "sends a SOCKS version reply"
        self._data_to_send(
            # for anonymous(0) *and* authenticated (2): struct.pack('BBBB', 5, 2, 0, 2)
            struct.pack('BBB', 5, 1, 0)
        )

    @_machine.output()
    def _disconnect(self, error):
        "done"
        if self._on_disconnect:
            self._on_disconnect(str(error))
        if self._sender:
            self._sender.connectionLost(Failure(error))
        self._when_done.fire(Failure(error))

    @_machine.output()
    def _send_request(self, auth_method):
        "send the request (connect, resolve or resolve_ptr)"
        assert auth_method == 0x00  # "no authentication required"
        return self._dispatch[self._req_type](self)

    @_machine.output()
    def _relay_data(self):
        "relay any data we have"
        if self._data:
            d = self._data
            self._data = b''
            # XXX this is "doing I/O" in the state-machine and it
            # really shouldn't be ... probably want a passed-in
            # "relay_data" callback or similar?
            self._sender.dataReceived(d)

    def _send_connect_request(self):
        "sends CONNECT request"
        # XXX needs to support v6 ... or something else does
        host = self._addr.host
        port = self._addr.port

        if isinstance(self._addr, (IPv4Address, IPv6Address)):
            is_v6 = isinstance(self._addr, IPv6Address)
            self._data_to_send(
                struct.pack(
                    '!BBBB4sH',
                    5,                   # version
                    0x01,                # command
                    0x00,                # reserved
                    0x04 if is_v6 else 0x01,
                    inet_pton(AF_INET6 if is_v6 else AF_INET, host),
                    port,
                )
            )
        else:
            host = host.encode('ascii')
            self._data_to_send(
                struct.pack(
                    '!BBBBB{}sH'.format(len(host)),
                    5,                   # version
                    0x01,                # command
                    0x00,                # reserved
                    0x03,
                    len(host),
                    host,
                    port,
                )
            )

    @_machine.output()
    def _send_resolve_request(self):
        "sends RESOLVE_PTR request (Tor custom)"
        host = self._addr.host.encode()
        self._data_to_send(
            struct.pack(
                '!BBBBB{}sH'.format(len(host)),
                5,                   # version
                0xF0,                # command
                0x00,                # reserved
                0x03,                # DOMAINNAME
                len(host),
                host,
                0,  # self._addr.port?
            )
        )

    @_machine.output()
    def _send_resolve_ptr_request(self):
        "sends RESOLVE_PTR request (Tor custom)"
        addr_type = 0x04 if isinstance(self._addr, ipaddress.IPv4Address) else 0x01
        encoded_host = inet_aton(self._addr.host)
        self._data_to_send(
            struct.pack(
                '!BBBB4sH',
                5,                   # version
                0xF1,                # command
                0x00,                # reserved
                addr_type,
                encoded_host,
                0,                   # port; unused? SOCKS is fun
            )
        )

    @_machine.state(initial=True)
    def unconnected(self):
        "not yet connected"

    @_machine.state()
    def sent_version(self):
        "we've sent our version request"

    @_machine.state()
    def sent_request(self):
        "we've sent our stream/etc request"

    @_machine.state()
    def relaying(self):
        "received our response, now we can relay"

    @_machine.state()
    def abort(self, error_message):
        "we've encountered an error"

    @_machine.state()
    def done(self):
        "operations complete"

    unconnected.upon(
        connection,
        enter=sent_version,
        outputs=[_send_version],
    )

    sent_version.upon(
        got_data,
        enter=sent_version,
        outputs=[_parse_version_reply],
    )
    sent_version.upon(
        version_error,
        enter=abort,
        outputs=[_disconnect],
    )
    sent_version.upon(
        version_reply,
        enter=sent_request,
        outputs=[_send_request],
    )
    sent_version.upon(
        disconnected,
        enter=unconnected,
        outputs=[_disconnect]
    )

    sent_request.upon(
        got_data,
        enter=sent_request,
        outputs=[_parse_request_reply],
    )
    sent_request.upon(
        reply_ipv4,
        enter=relaying,
        outputs=[_make_connection],
    )
    sent_request.upon(
        reply_ipv6,
        enter=relaying,
        outputs=[_make_connection],
    )
    # XXX this isn't always a _domain_name_resolved -- if we're a
    # req_type CONNECT then it's _make_connection_domain ...
    sent_request.upon(
        reply_domain_name,
        enter=done,
        outputs=[_domain_name_resolved],
    )
    sent_request.upon(
        reply_error,
        enter=abort,
        outputs=[_disconnect],
    )
# XXX FIXME this needs a test
    sent_request.upon(
        disconnected,
        enter=abort,
        outputs=[_disconnect],  # ... or is this redundant?
    )

    relaying.upon(
        got_data,
        enter=relaying,
        outputs=[_relay_data],
    )
    relaying.upon(
        disconnected,
        enter=done,
        outputs=[_disconnect],
    )

    abort.upon(
        got_data,
        enter=abort,
        outputs=[],
    )
    abort.upon(
        disconnected,
        enter=abort,
        outputs=[],
    )

    done.upon(
        disconnected,
        enter=done,
        outputs=[],
    )

    _dispatch = {
        'CONNECT': _send_connect_request,
        'RESOLVE': _send_resolve_request,
        'RESOLVE_PTR': _send_resolve_ptr_request,
    }


class _TorSocksProtocol(Protocol):

    def __init__(self, host, port, socks_method, factory):
        self._machine = _SocksMachine(
            req_type=socks_method,
            host=host,  # noqa unicode() on py3, py2? we want idna, actually?
            port=port,
            on_disconnect=self._on_disconnect,
            on_data=self._on_data,
            create_connection=self._create_connection,
        )
        self._factory = factory

    def when_done(self):
        return self._machine.when_done()

    def connectionMade(self):
        self._machine.connection()
        # we notify via the factory that we have teh
        # locally-connecting host -- this is e.g. used by the "stream
        # over one particular circuit" code to determine the local
        # port that "our" SOCKS connection went to
        self.factory._did_connect(self.transport.getHost())

    def connectionLost(self, reason):
        self._machine.disconnected(SocksError(reason))

    def dataReceived(self, data):
        self._machine.feed_data(data)

    def _on_data(self, data):
        self.transport.write(data)

    def _create_connection(self, addr, port):
        addr = IPv4Address('TCP', addr, port)
        sender = self._factory.buildProtocol(addr)
        client_proxy = portforward.ProxyClient()
        sender.makeConnection(self.transport)
        # portforward.ProxyClient is going to call setPeer but this
        # probably doesn't have it...
        setattr(sender, 'setPeer', lambda _: None)
        client_proxy.setPeer(sender)
        self._sender = sender
        return sender

    def _on_disconnect(self, error_message):
        self.transport.loseConnection()
        # self.transport.abortConnection()#SocksError(error_message)) ?


class _TorSocksFactory(Factory):
    protocol = _TorSocksProtocol

    # XXX should do validation on this stuff so we get errors before
    # building the protocol
    def __init__(self, *args, **kw):
        self._args = args
        self._kw = kw
        self._host = None
        self._when_connected = util.SingleObserver()

    def _get_address(self):
        """
        Returns a Deferred that fires with the transport's getHost()
        when this SOCKS protocol becomes connected.
        """
        return self._when_connected.when_fired()

    def _did_connect(self, host):
        self._host = host
        self._when_connected.fire(host)

    def buildProtocol(self, addr):
        p = self.protocol(*self._args, **self._kw)
        p.factory = self
        return p


class SocksError(Exception):
    code = None
    message = ''

    def __init__(self, message='', code=None):
        super(SocksError, self).__init__(message or self.message)
        self.message = message or self.message
        self.code = code or self.code


class GeneralServerFailureError(SocksError):
    code = 0x01
    message = 'general SOCKS server failure'


class ConnectionNotAllowedError(SocksError):
    code = 0x02
    message = 'connection not allowed by ruleset'


class NetworkUnreachableError(SocksError):
    code = 0x03
    message = 'Network unreachable'


class HostUnreachableError(SocksError):
    code = 0x04
    message = 'Host unreachable'


class ConnectionRefusedError(SocksError):
    code = 0x05
    message = 'Connection refused'


class TtlExpiredError(SocksError):
    code = 0x06
    message = 'TTL expired'


class CommandNotSupportedError(SocksError):
    code = 0x07
    message = 'Command not supported'


class AddressTypeNotSupportedError(SocksError):
    code = 0x08
    message = 'Address type not supported'


_socks_errors = {cls.code: cls for cls in SocksError.__subclasses__()}


def _create_socks_error(code):
    try:
        return _socks_errors[code]()
    except KeyError:
        return SocksError("Unknown SOCKS error-code {}".format(code),
                          code=code)


@inlineCallbacks
def resolve(tor_endpoint, hostname):
    """
    This is easier to use via :meth:`txtorcon.Tor.dns_resolve`

    :param tor_endpoint: the Tor SOCKS endpoint to use.

    :param hostname: the hostname to look up.
    """
    if six.PY2 and isinstance(hostname, str):
        hostname = unicode(hostname)  # noqa
    elif six.PY3 and isinstance(hostname, bytes):
        hostname = hostname.decode('ascii')
    factory = _TorSocksFactory(
        hostname, 0, 'RESOLVE', None,
    )
    proto = yield tor_endpoint.connect(factory)
    result = yield proto.when_done()
    returnValue(result)


@inlineCallbacks
def resolve_ptr(tor_endpoint, ip):
    """
    This is easier to use via :meth:`txtorcon.Tor.dns_resolve_ptr`

    :param tor_endpoint: the Tor SOCKS endpoint to use.

    :param ip: the IP address to look up.
    """
    if six.PY2 and isinstance(ip, str):
        ip = unicode(ip)  # noqa
    elif six.PY3 and isinstance(ip, bytes):
        ip = ip.decode('ascii')
    factory = _TorSocksFactory(
        ip, 0, 'RESOLVE_PTR', None,
    )
    proto = yield tor_endpoint.connect(factory)
    result = yield proto.when_done()
    returnValue(result)


@implementer(IStreamClientEndpoint)
class TorSocksEndpoint(object):
    """
    Represents an endpoint which will talk to a Tor SOCKS port.

    These should usually not be instantiated directly, instead use
    :meth:`txtorcon.TorConfig.socks_endpoint`.
    """
    # XXX host, port args should be (host, port) tuple, or
    # IAddress-implementer?
    def __init__(self, socks_endpoint, host, port, tls=False):
        self._proxy_ep = socks_endpoint  # can be Deferred
        assert self._proxy_ep is not None
        if six.PY2 and isinstance(host, str):
            host = unicode(host)  # noqa
        if six.PY3 and isinstance(host, bytes):
            host = host.decode('ascii')
        self._host = host
        self._port = port
        self._tls = tls
        self._socks_factory = None
        self._when_address = util.SingleObserver()

    def _get_address(self):
        """
        Returns a Deferred that fires with the source IAddress of the
        underlying SOCKS connection (i.e. usually a
        twisted.internet.address.IPv4Address)

        circuit.py uses this; better suggestions welcome!
        """
        return self._when_address.when_fired()

    @inlineCallbacks
    def connect(self, factory):
        # further wrap the protocol if we're doing TLS.
        # "pray i do not wrap the protocol further".
        if self._tls:
            # XXX requires Twisted 14+
            from twisted.internet.ssl import optionsForClientTLS
            if self._tls is True:
                context = optionsForClientTLS(self._host)
            else:
                context = self._tls
            tls_factory = tls.TLSMemoryBIOFactory(context, True, factory)
            socks_factory = _TorSocksFactory(
                self._host, self._port, 'CONNECT', tls_factory,
            )
        else:
            socks_factory = _TorSocksFactory(
                self._host, self._port, 'CONNECT', factory,
            )

        self._socks_factory = socks_factory
        # forward our address (when we get it) to any listeners
        self._socks_factory._get_address().addBoth(self._when_address.fire)
        # XXX isn't this just maybeDeferred()
        if isinstance(self._proxy_ep, Deferred):
            proxy_ep = yield self._proxy_ep
            if not IStreamClientEndpoint.providedBy(proxy_ep):
                raise ValueError(
                    "The Deferred provided as 'socks_endpoint' must "
                    "resolve to an IStreamClientEndpoint provider (got "
                    "{})".format(type(proxy_ep).__name__)
                )
        else:
            proxy_ep = self._proxy_ep

        # socks_proto = yield proxy_ep.connect(socks_factory)
        proto = yield proxy_ep.connect(socks_factory)
        wrapped_proto = yield proto.when_done()
        if self._tls:
            returnValue(wrapped_proto.wrappedProtocol)
        else:
            returnValue(wrapped_proto)
