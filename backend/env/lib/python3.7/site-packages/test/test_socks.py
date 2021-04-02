from six import BytesIO, text_type
from mock import Mock, patch

from twisted.trial import unittest
from twisted.internet import defer
from twisted.internet.address import IPv4Address
from twisted.internet.protocol import Protocol
from twisted.test import proto_helpers
from twisted.test.iosim import connect, FakeTransport

from txtorcon import socks


class SocksStateMachine(unittest.TestCase):

    def test_illegal_request(self):
        with self.assertRaises(ValueError) as ctx:
            socks._SocksMachine('FOO_RESOLVE', u'meejah.ca', 443)
        self.assertTrue(
            'Unknown request type' in str(ctx.exception)
        )

    def test_illegal_host(self):
        with self.assertRaises(ValueError) as ctx:
            socks._SocksMachine('RESOLVE', 1234, 443)
        self.assertTrue(
            "'host' must be" in str(ctx.exception)
        )

    def test_illegal_ip_addr(self):
        with self.assertRaises(ValueError) as ctx:
            socks._create_ip_address(1234, 443)
        self.assertTrue(
            "'host' must be" in str(ctx.exception)
        )

    def test_connect_but_no_creator(self):
        with self.assertRaises(ValueError) as ctx:
            socks._SocksMachine(
                'CONNECT', u'foo.bar',
            )
        self.assertTrue(
            "create_connection function required" in str(ctx.exception)
        )

    @defer.inlineCallbacks
    def test_connect_socks_illegal_packet(self):

        class BadSocksServer(Protocol):
            def __init__(self):
                self._buffer = b''

            def dataReceived(self, data):
                self._buffer += data
                if len(self._buffer) == 3:
                    assert self._buffer == b'\x05\x01\x00'
                    self._buffer = b''
                    self.transport.write(b'\x05\x01\x01')

        factory = socks._TorSocksFactory(u'meejah.ca', 1234, 'CONNECT', Mock())
        server_proto = BadSocksServer()
        server_transport = FakeTransport(server_proto, isServer=True)

        client_proto = factory.buildProtocol('ignored')
        client_transport = FakeTransport(client_proto, isServer=False)

        pump = yield connect(
            server_proto, server_transport,
            client_proto, client_transport,
        )

        self.assertTrue(server_proto.transport.disconnected)
        self.assertTrue(client_proto.transport.disconnected)
        pump.flush()

    @defer.inlineCallbacks
    def test_connect_socks_unknown_version(self):

        class BadSocksServer(Protocol):
            def __init__(self):
                self._buffer = b''
                self._recv_stack = [
                    (b'\x05\x01\x00', b'\x05\xff'),
                ]

            def dataReceived(self, data):
                self._buffer += data
                if len(self._recv_stack) == 0:
                    assert "not expecting any more data, got {}".format(repr(self._buffer))
                    return
                expecting, to_send = self._recv_stack.pop(0)
                got = self._buffer[:len(expecting)]
                self._buffer = self._buffer[len(expecting):]
                assert got == expecting, "wanted {} but got {}".format(repr(expecting), repr(got))
                self.transport.write(to_send)

        factory = socks._TorSocksFactory(u'1.2.3.4', 1234, 'CONNECT', Mock())
        server_proto = BadSocksServer()
        server_transport = FakeTransport(server_proto, isServer=True)

        client_proto = factory.buildProtocol('ignored')
        client_transport = FakeTransport(client_proto, isServer=False)

        # returns IOPump
        yield connect(
            server_proto, server_transport,
            client_proto, client_transport,
        )

        self.assertTrue(server_proto.transport.disconnected)
        self.assertTrue(client_proto.transport.disconnected)

    @defer.inlineCallbacks
    def test_connect_socks_unknown_reply_code(self):

        class BadSocksServer(Protocol):
            def __init__(self):
                self._buffer = b''
                self._recv_stack = [
                    (b'\x05\x01\x00', b'\x05\x00'),
                    # the \xff is an invalid reply-code
                    (b'\x05\x01\x00\x01\x01\x02\x03\x04\x04\xd2', b'\x05\xff\x00\x04\x01\x01\x01\x01'),
                ]

            def dataReceived(self, data):
                self._buffer += data
                if len(self._recv_stack) == 0:
                    assert "not expecting any more data, got {}".format(repr(self._buffer))
                    return
                expecting, to_send = self._recv_stack.pop(0)
                got = self._buffer[:len(expecting)]
                self._buffer = self._buffer[len(expecting):]
                assert got == expecting, "wanted {} but got {}".format(repr(expecting), repr(got))
                self.transport.write(to_send)

        factory = socks._TorSocksFactory(u'1.2.3.4', 1234, 'CONNECT', Mock())
        server_proto = BadSocksServer()
        server_transport = FakeTransport(server_proto, isServer=True)

        client_proto = factory.buildProtocol('ignored')
        client_transport = FakeTransport(client_proto, isServer=False)

        d = client_proto._machine.when_done()

        # returns IOPump
        yield connect(
            server_proto, server_transport,
            client_proto, client_transport,
        )
        with self.assertRaises(Exception) as ctx:
            yield d
        self.assertIn('Unknown SOCKS error-code', str(ctx.exception))

    @defer.inlineCallbacks
    def test_socks_relay_data(self):

        class BadSocksServer(Protocol):
            def __init__(self):
                self._buffer = b''
                self._recv_stack = [
                    (b'\x05\x01\x00', b'\x05\x00'),
                    (b'\x05\x01\x00\x01\x01\x02\x03\x04\x04\xd2', b'\x05\x00\x00\x01\x01\x02\x03\x04\x12\x34'),
                ]

            def dataReceived(self, data):
                self._buffer += data
                if len(self._recv_stack) == 0:
                    assert "not expecting any more data, got {}".format(repr(self._buffer))
                    return
                expecting, to_send = self._recv_stack.pop(0)
                got = self._buffer[:len(expecting)]
                self._buffer = self._buffer[len(expecting):]
                assert got == expecting, "wanted {} but got {}".format(repr(expecting), repr(got))
                self.transport.write(to_send)

        factory = socks._TorSocksFactory(u'1.2.3.4', 1234, 'CONNECT', Mock())
        server_proto = BadSocksServer()
        server_transport = FakeTransport(server_proto, isServer=True)

        client_proto = factory.buildProtocol('ignored')
        client_transport = FakeTransport(client_proto, isServer=False)

        pump = yield connect(
            server_proto, server_transport,
            client_proto, client_transport,
        )

        # should be relaying now, try sending some datas

        client_proto.transport.write(b'abcdef')
        pump.flush()
        self.assertEqual(b'abcdef', server_proto._buffer)

    @defer.inlineCallbacks
    def test_socks_ipv6(self):

        class BadSocksServer(Protocol):
            def __init__(self):
                self._buffer = b''
                self._recv_stack = [
                    (b'\x05\x01\x00', b'\x05\x00'),
                    (b'\x05\x01\x00\x04\x20\x02\x44\x93\x04\xd2',
                     b'\x05\x00\x00\x04' + (b'\x00' * 16) + b'\xbe\xef'),
                ]

            def dataReceived(self, data):
                self._buffer += data
                if len(self._recv_stack) == 0:
                    assert "not expecting any more data, got {}".format(repr(self._buffer))
                    return
                expecting, to_send = self._recv_stack.pop(0)
                got = self._buffer[:len(expecting)]
                self._buffer = self._buffer[len(expecting):]
                assert got == expecting, "wanted {} but got {}".format(repr(expecting), repr(got))
                self.transport.write(to_send)

        factory = socks._TorSocksFactory(u'2002:4493:5105::a299:9bff:fe0e:4471', 1234, 'CONNECT', Mock())
        server_proto = BadSocksServer()
        expected_address = object()
        server_transport = FakeTransport(server_proto, isServer=True)

        client_proto = factory.buildProtocol(u'ignored')
        client_transport = FakeTransport(client_proto, isServer=False, hostAddress=expected_address)

        pump = yield connect(
            server_proto, server_transport,
            client_proto, client_transport,
        )

        # should be relaying now, try sending some datas

        client_proto.transport.write(b'abcdef')
        addr = yield factory._get_address()

        # FIXME how shall we test for IPv6-ness?
        assert addr is expected_address
        pump.flush()
        self.assertEqual(b'abcdef', server_proto._buffer)

    def test_end_to_end_wrong_method(self):
        dis = []

        def on_disconnect(error_message):
            dis.append(error_message)
        sm = socks._SocksMachine('RESOLVE', u'meejah.ca', 443, on_disconnect=on_disconnect)
        sm.connection()

        sm.feed_data(b'\x05')
        sm.feed_data(b'\x01')

        # we should have sent the request to the server, and nothing
        # else (because we disconnected)
        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00',
            data.getvalue(),
        )
        self.assertEqual(1, len(dis))
        self.assertEqual("Wanted method 0 or 2, got 1", dis[0])

    def test_end_to_end_wrong_version(self):
        dis = []

        def on_disconnect(error_message):
            dis.append(error_message)
        sm = socks._SocksMachine('RESOLVE', u'meejah.ca', 443, on_disconnect=on_disconnect)
        sm.connection()

        sm.feed_data(b'\x06')
        sm.feed_data(b'\x00')

        # we should have sent the request to the server, and nothing
        # else (because we disconnected)
        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00',
            data.getvalue(),
        )
        self.assertEqual(1, len(dis))
        self.assertEqual("Expected version 5, got 6", dis[0])

    def test_end_to_end_connection_refused(self):
        dis = []

        def on_disconnect(error_message):
            dis.append(error_message)
        sm = socks._SocksMachine(
            'CONNECT', u'1.2.3.4', 443,
            on_disconnect=on_disconnect,
            create_connection=lambda a, p: None,
        )
        sm.connection()

        sm.feed_data(b'\x05')
        sm.feed_data(b'\x00')

        # reply with 'connection refused'
        sm.feed_data(b'\x05\x05\x00\x01\x00\x00\x00\x00\xff\xff')

        self.assertEqual(1, len(dis))
        self.assertEqual(socks.ConnectionRefusedError.message, dis[0])

    def test_end_to_end_successful_relay(self):

        class Proto(object):
            data = b''
            lost = []

            def dataReceived(self, d):
                self.data = self.data + d

            def connectionLost(self, reason):
                self.lost.append(reason)

        the_proto = Proto()
        dis = []

        def on_disconnect(error_message):
            dis.append(error_message)
        sm = socks._SocksMachine(
            'CONNECT', u'1.2.3.4', 443,
            on_disconnect=on_disconnect,
            create_connection=lambda a, p: the_proto,
        )
        sm.connection()

        sm.feed_data(b'\x05')
        sm.feed_data(b'\x00')

        # reply with success, port 0x1234
        sm.feed_data(b'\x05\x00\x00\x01\x00\x00\x00\x00\x12\x34')

        # now some data that should get relayed
        sm.feed_data(b'this is some relayed data')
        # should *not* have disconnected
        self.assertEqual(0, len(dis))
        self.assertTrue(the_proto.data, b"this is some relayed data")
        sm.disconnected(socks.SocksError("it's fine"))
        self.assertEqual(1, len(Proto.lost))
        self.assertTrue("it's fine" in str(Proto.lost[0]))

    def test_end_to_end_success(self):
        sm = socks._SocksMachine('RESOLVE', u'meejah.ca', 443)
        sm.connection()

        sm.feed_data(b'\x05')
        sm.feed_data(b'\x00')

        # now we check we got the right bytes out the other side
        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00'
            b'\x05\xf0\x00\x03\tmeejah.ca\x00\x00',
            data.getvalue(),
        )

    def test_end_to_end_connect_and_relay(self):
        sm = socks._SocksMachine(
            'CONNECT', u'1.2.3.4', 443,
            create_connection=lambda a, p: None,
        )
        sm.connection()

        sm.feed_data(b'\x05')
        sm.feed_data(b'\x00')
        sm.feed_data(b'some relayed data')

        # now we check we got the right bytes out the other side
        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00'
            b'\x05\x01\x00\x01\x01\x02\x03\x04\x01\xbb',
            data.getvalue(),
        )

    def test_resolve(self):
        # kurt: most things use (hsot, port) tuples, this probably
        # should too
        sm = socks._SocksMachine('RESOLVE', u'meejah.ca', 443)
        sm.connection()
        sm.version_reply(0x00)

        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00'
            b'\x05\xf0\x00\x03\tmeejah.ca\x00\x00',
            data.getvalue(),
        )

    @defer.inlineCallbacks
    def test_resolve_with_reply(self):
        # kurt: most things use (hsot, port) tuples, this probably
        # should too
        sm = socks._SocksMachine('RESOLVE', u'meejah.ca', 443)
        sm.connection()
        sm.version_reply(0x00)

        # make sure the state-machine wanted to send out the correct
        # request.
        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00'
            b'\x05\xf0\x00\x03\tmeejah.ca\x00\x00',
            data.getvalue(),
        )

        # now feed it a reply (but not enough to parse it yet!)
        d = sm.when_done()
        # ...we have to send at least 8 bytes, but NOT the entire hostname
        sm.feed_data(b'\x05\x00\x00\x03')
        sm.feed_data(b'\x06meeja')
        self.assertTrue(not d.called)
        # now send the rest, checking the buffering in _parse_domain_name_reply
        sm.feed_data(b'h\x00\x00')
        self.assertTrue(d.called)
        answer = yield d
        # XXX answer *should* be not-bytes, though I think
        self.assertEqual(b'meejah', answer)

    @defer.inlineCallbacks
    def test_unknown_response_type(self):
        # kurt: most things use (hsot, port) tuples, this probably
        # should too
        sm = socks._SocksMachine('RESOLVE', u'meejah.ca', 443)
        sm.connection()
        # don't actually support username/password (which is version 0x02) yet
        # sm.version_reply(0x02)
        sm.version_reply(0)

        # make sure the state-machine wanted to send out the correct
        # request.
        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00'
            b'\x05\xf0\x00\x03\tmeejah.ca\x00\x00',
            data.getvalue(),
        )

        sm.feed_data(b'\x05\x00\x00\xaf\x00\x00\x00\x00')
        with self.assertRaises(socks.SocksError) as ctx:
            yield sm.when_done()
        self.assertTrue('Unexpected response type 175' in str(ctx.exception))

    @defer.inlineCallbacks
    def test_resolve_ptr(self):
        sm = socks._SocksMachine('RESOLVE_PTR', u'1.2.3.4', 443)
        sm.connection()
        sm.version_reply(0x00)

        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00'
            b'\x05\xf1\x00\x01\x01\x02\x03\x04\x00\x00',
            data.getvalue(),
        )
        sm.feed_data(
            b'\x05\x00\x00\x01\x00\x01\x02\xff\x12\x34'
        )
        addr = yield sm.when_done()
        self.assertEqual('0.1.2.255', addr)

    def test_connect(self):
        sm = socks._SocksMachine(
            'CONNECT', u'1.2.3.4', 443,
            create_connection=lambda a, p: None,
        )
        sm.connection()
        sm.version_reply(0x00)

        data = BytesIO()
        sm.send_data(data.write)
        self.assertEqual(
            b'\x05\x01\x00'
            b'\x05\x01\x00\x01\x01\x02\x03\x04\x01\xbb',
            data.getvalue(),
        )


# XXX should re-write (at LEAST) these to use Twisted's IOPump
class SocksConnectTests(unittest.TestCase):

    @defer.inlineCallbacks
    def test_connect_no_tls(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            self.assertEqual(b'\x05\x01\x00', transport.value())
            proto.dataReceived(b'\x05\x00')
            proto.dataReceived(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            return proto
        socks_ep.connect = connect
        protocol = Mock()
        factory = Mock()
        factory.buildProtocol = Mock(return_value=protocol)
        ep = socks.TorSocksEndpoint(socks_ep, u'meejah.ca', 443)
        proto = yield ep.connect(factory)
        self.assertEqual(proto, protocol)

    @defer.inlineCallbacks
    def test_connect_deferred_proxy(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            self.assertEqual(b'\x05\x01\x00', transport.value())
            proto.dataReceived(b'\x05\x00')
            proto.dataReceived(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            return proto
        socks_ep.connect = connect
        protocol = Mock()
        factory = Mock()
        factory.buildProtocol = Mock(return_value=protocol)
        ep = socks.TorSocksEndpoint(
            socks_endpoint=defer.succeed(socks_ep),
            host=u'meejah.ca',
            port=443,
        )
        proto = yield ep.connect(factory)
        self.assertEqual(proto, protocol)

    @defer.inlineCallbacks
    def test_connect_tls(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            self.assertEqual(b'\x05\x01\x00', transport.value())
            proto.dataReceived(b'\x05\x00')
            proto.dataReceived(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            return proto
        socks_ep.connect = connect
        protocol = Mock()
        factory = Mock()
        factory.buildProtocol = Mock(return_value=protocol)
        ep = socks.TorSocksEndpoint(socks_ep, u'meejah.ca', 443, tls=True)
        proto = yield ep.connect(factory)
        self.assertEqual(proto, protocol)

    @defer.inlineCallbacks
    def test_connect_socks_error(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            self.assertEqual(b'\x05\x01\x00', transport.value())
            proto.dataReceived(b'\x05\x00')
            proto.dataReceived(b'\x05\x01\x00\x01\x00\x00\x00\x00')
            return proto
        socks_ep.connect = connect
        protocol = Mock()
        factory = Mock()
        factory.buildProtocol = Mock(return_value=protocol)
        ep = socks.TorSocksEndpoint(socks_ep, u'meejah.ca', 443, tls=True)
        with self.assertRaises(Exception) as ctx:
            yield ep.connect(factory)
        self.assertTrue(isinstance(ctx.exception,
                                   socks.GeneralServerFailureError))

    @defer.inlineCallbacks
    def test_connect_socks_error_unknown(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            self.assertEqual(b'\x05\x01\x00', transport.value())
            proto.dataReceived(b'\x05\x00')
            proto.dataReceived(b'\x05\xff\x00\x01\x00\x00\x00\x00')
            return proto
        socks_ep.connect = connect
        protocol = Mock()
        factory = Mock()
        factory.buildProtocol = Mock(return_value=protocol)
        ep = socks.TorSocksEndpoint(socks_ep, u'meejah.ca', 443, tls=True)
        with self.assertRaises(Exception) as ctx:
            yield ep.connect(factory)
        self.assertTrue('Unknown SOCKS error-code' in str(ctx.exception))

    @defer.inlineCallbacks
    def test_connect_socks_illegal_byte(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            self.assertEqual(b'\x05\x01\x00', transport.value())
            proto.dataReceived(b'\x05\x00')
            proto.dataReceived(b'\x05\x01\x00\x01\x00\x00\x00\x00')
            return proto
        socks_ep.connect = connect
        protocol = Mock()
        factory = Mock()
        factory.buildProtocol = Mock(return_value=protocol)
        ep = socks.TorSocksEndpoint(socks_ep, u'meejah.ca', 443, tls=True)
        with self.assertRaises(Exception) as ctx:
            yield ep.connect(factory)
        self.assertTrue(isinstance(ctx.exception,
                                   socks.GeneralServerFailureError))

    @defer.inlineCallbacks
    def test_get_address_endpoint(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()
        delayed_addr = []

        def connect(factory):
            delayed_addr.append(factory._get_address())
            delayed_addr.append(factory._get_address())
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            self.assertEqual(b'\x05\x01\x00', transport.value())
            proto.dataReceived(b'\x05\x00')
            proto.dataReceived(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            return proto
        socks_ep.connect = connect
        protocol = Mock()
        factory = Mock()
        factory.buildProtocol = Mock(return_value=protocol)
        ep = socks.TorSocksEndpoint(socks_ep, u'meejah.ca', 443, tls=True)
        yield ep.connect(factory)
        addr = yield ep._get_address()

        self.assertEqual(addr, IPv4Address('TCP', '10.0.0.1', 12345))
        self.assertEqual(2, len(delayed_addr))
        self.assertTrue(delayed_addr[0] is not delayed_addr[1])
        self.assertTrue(all([d.called for d in delayed_addr]))

    @defer.inlineCallbacks
    def test_get_address(self):
        # normally, ._get_address is only called via the
        # attach_stream() method on Circuit
        addr = object()
        factory = socks._TorSocksFactory()
        d = factory._get_address()
        self.assertFalse(d.called)
        factory._did_connect(addr)

        maybe_addr = yield d

        self.assertEqual(addr, maybe_addr)

        # if we do it a second time, should be immediate
        d = factory._get_address()
        self.assertTrue(d.called)
        self.assertEqual(d.result, addr)


class SocksResolveTests(unittest.TestCase):

    @defer.inlineCallbacks
    def test_resolve(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            # XXX sadness: we probably "should" just feed the right
            # bytes to the protocol to convince it a connection is
            # made ... *or* we can cheat and just do the callback
            # directly...
            proto._machine._when_done.fire("the dns answer")
            return proto
        socks_ep.connect = connect
        hn = yield socks.resolve(socks_ep, u'meejah.ca')
        self.assertEqual(hn, "the dns answer")

    @defer.inlineCallbacks
    def test_resolve_ptr(self):
        socks_ep = Mock()
        transport = proto_helpers.StringTransport()

        def connect(factory):
            factory.startFactory()
            proto = factory.buildProtocol("addr")
            proto.makeConnection(transport)
            # XXX sadness: we probably "should" just feed the right
            # bytes to the protocol to convince it a connection is
            # made ... *or* we can cheat and just do the callback
            # directly...
            proto._machine._when_done.fire(u"the dns answer")
            return proto
        socks_ep.connect = connect
        hn = yield socks.resolve_ptr(socks_ep, u'meejah.ca')
        self.assertEqual(hn, "the dns answer")

    @patch('txtorcon.socks._TorSocksFactory')
    def test_resolve_ptr_str(self, fac):
        socks_ep = Mock()
        d = socks.resolve_ptr(socks_ep, 'meejah.ca')
        self.assertEqual(1, len(fac.mock_calls))
        self.assertTrue(
            isinstance(fac.mock_calls[0][1][0], text_type)
        )
        return d

    @patch('txtorcon.socks._TorSocksFactory')
    def test_resolve_str(self, fac):
        socks_ep = Mock()
        d = socks.resolve(socks_ep, 'meejah.ca')
        self.assertEqual(1, len(fac.mock_calls))
        self.assertTrue(
            isinstance(fac.mock_calls[0][1][0], text_type)
        )
        return d

    @patch('txtorcon.socks._TorSocksFactory')
    def test_resolve_ptr_bytes(self, fac):
        socks_ep = Mock()
        d = socks.resolve_ptr(socks_ep, b'meejah.ca')
        self.assertEqual(1, len(fac.mock_calls))
        self.assertTrue(
            isinstance(fac.mock_calls[0][1][0], text_type)
        )
        return d

    @patch('txtorcon.socks._TorSocksFactory')
    def test_resolve_bytes(self, fac):
        socks_ep = Mock()
        d = socks.resolve(socks_ep, b'meejah.ca')
        self.assertEqual(1, len(fac.mock_calls))
        self.assertTrue(
            isinstance(fac.mock_calls[0][1][0], text_type)
        )
        return d


class SocksErrorTests(unittest.TestCase):
    def _check_error(self, error, cls_, code, message):
        self.assertTrue(isinstance(error, cls_))
        self.assertEqual(error.code, code)
        self.assertEqual(error.message, message)
        self.assertEqual(str(error), message)

    def test_error_factory(self):
        for cls in socks.SocksError.__subclasses__():
            error = socks._create_socks_error(cls.code)
            self._check_error(error, cls, cls.code, cls.message)

    def test_custom_error(self):
        code = 0xFF
        message = 'Custom error message'

        self._check_error(socks.SocksError(message),
                          socks.SocksError, None, message)
        self._check_error(socks.SocksError(message=message),
                          socks.SocksError, None, message)
        self._check_error(socks.SocksError(code=code),
                          socks.SocksError, code, '')
        self._check_error(socks.SocksError(message, code=code),
                          socks.SocksError, code, message)
        self._check_error(socks.SocksError(message=message, code=code),
                          socks.SocksError, code, message)
