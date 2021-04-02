from __future__ import print_function

import os
from mock import patch
from mock import Mock, MagicMock

from zope.interface import implementer, directlyProvides

from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet import defer, error, tcp, unix
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.endpoints import UNIXClientEndpoint
from twisted.internet.endpoints import serverFromString
from twisted.internet.endpoints import clientFromString
from twisted.python.failure import Failure
from twisted.internet.error import ConnectionRefusedError
from twisted.internet.interfaces import IStreamClientEndpoint
from twisted.internet.interfaces import IReactorCore
from twisted.internet.interfaces import IProtocol
from twisted.internet.interfaces import IReactorTCP
from twisted.internet.interfaces import IListeningPort
from twisted.internet.interfaces import IAddress

from txtorcon import TorControlProtocol
from txtorcon import TorConfig
from txtorcon import TCPHiddenServiceEndpoint
from txtorcon import TorClientEndpoint
# from txtorcon import TorClientEndpointStringParser
from txtorcon import IProgressProvider
from txtorcon import TorOnionAddress
from txtorcon.util import NoOpProtocolFactory
from txtorcon.util import SingleObserver
from txtorcon.endpoints import get_global_tor                       # FIXME
from txtorcon.endpoints import _create_socks_endpoint
from txtorcon.circuit import TorCircuitEndpoint, _get_circuit_attacher
from txtorcon.controller import Tor
from txtorcon.socks import _TorSocksFactory

from . import util
from .test_torconfig import FakeControlProtocol  # FIXME


@implementer(IReactorCore)
class MockReactor(Mock):
    """
    Just so that our 'provides IReactorCore' assertions pass, but it's
    still "just a Mock".
    """
    pass


@patch('txtorcon.controller.find_tor_binary', return_value='/bin/echo')
class EndpointTests(unittest.TestCase):

    def setUp(self):
        from txtorcon import endpoints
        endpoints._global_tor_config = None
        del endpoints._global_tor_lock
        endpoints._global_tor_lock = defer.DeferredLock()
        self.reactor = FakeReactorTcp(self)
        self.protocol = FakeControlProtocol([])
        self.protocol.event_happened('INFO', 'something craaaaaaazy')
        self.protocol.event_happened(
            'INFO',
            'connection_dir_client_reached_eof(): Uploaded rendezvous '
            'descriptor (status 200 ("Service descriptor (v2) stored"))'
        )
        self.config = TorConfig(self.protocol)
        self.protocol.answers.append(
            'config/names=\nHiddenServiceOptions Virtual\nControlPort LineList'
        )
        self.protocol.answers.append('HiddenServiceOptions')
        # why do i have to pass a dict for this V but not this ^
        self.protocol.answers.append({'ControlPort': '37337'})
        self.patcher = patch(
            'txtorcon.controller.find_tor_binary',
            return_value='/not/tor'
        )
        self.patcher.start()

    def tearDown(self):
        from txtorcon import endpoints
        endpoints._global_tor_config = None
        del endpoints._global_tor_lock
        endpoints._global_tor_lock = defer.DeferredLock()
        self.patcher.stop()

    @defer.inlineCallbacks
    def test_global_tor(self, ftb):
        config = yield get_global_tor(
            Mock(),
            _tor_launcher=lambda x, y, z: True
        )
        self.assertEqual(0, config.SOCKSPort)

    @defer.inlineCallbacks
    def test_global_tor_error(self, ftb):
        yield get_global_tor(
            reactor=Mock(),
            _tor_launcher=lambda x, y, z: True
        )
        # now if we specify a control_port it should be an error since
        # the above should have launched one.
        try:
            yield get_global_tor(
                reactor=Mock(),
                control_port=111,
                _tor_launcher=lambda x, y, z: True
            )
            self.fail()
        except RuntimeError:
            # should be an error
            pass

    @defer.inlineCallbacks
    def test_endpoint_properties(self, ftb):
        ep = yield TCPHiddenServiceEndpoint.private_tor(self.reactor, 80)
        self.assertEqual(None, ep.onion_private_key)
        self.assertEqual(None, ep.onion_uri)
        ep.hiddenservice = Mock()
        ep.hiddenservice.private_key = 'mumble'
        self.assertEqual('mumble', ep.onion_private_key)

    @defer.inlineCallbacks
    def test_private_tor(self, ftb):
        m = Mock()
        from txtorcon import endpoints
        endpoints.launch_tor = m
        yield TCPHiddenServiceEndpoint.private_tor(
            Mock(), 80,
            control_port=1234,
        )
        self.assertTrue(m.called)

    @defer.inlineCallbacks
    def test_private_tor_no_control_port(self, ftb):
        m = Mock()
        from txtorcon import endpoints
        endpoints.launch_tor = m
        yield TCPHiddenServiceEndpoint.private_tor(Mock(), 80)
        self.assertTrue(m.called)

    @defer.inlineCallbacks
    def test_system_tor(self, ftb):

        def boom():
            # why does the new_callable thing need a callable that
            # returns a callable? Feels like I must be doing something
            # wrong somewhere...
            def bam(*args, **kw):
                self.config.bootstrap()
                return defer.succeed(Tor(Mock(), self.protocol, _tor_config=self.config))
            return bam
        with patch('txtorcon.endpoints.launch_tor') as launch_mock:
            with patch('txtorcon.controller.connect', new_callable=boom):
                client = clientFromString(
                    self.reactor,
                    "tcp:host=localhost:port=9050"
                )
                ep = yield TCPHiddenServiceEndpoint.system_tor(self.reactor,
                                                               client, 80)
                port = yield ep.listen(NoOpProtocolFactory())
                toa = port.getHost()
                self.assertTrue(hasattr(toa, 'onion_uri'))
                self.assertTrue(hasattr(toa, 'onion_port'))
                port.startListening()
                str(port)
                port.tor_config
                # system_tor should be connecting to a running one,
                # *not* launching a new one.
                self.assertFalse(launch_mock.called)

    @defer.inlineCallbacks
    def test_basic(self, ftb):
        listen = RuntimeError("listen")
        connect = RuntimeError("connect")
        reactor = proto_helpers.RaisingMemoryReactor(listen, connect)
        reactor.addSystemEventTrigger = Mock()

        ep = TCPHiddenServiceEndpoint(reactor, self.config, 123)
        self.config.bootstrap()
        yield self.config.post_bootstrap
        self.assertTrue(IProgressProvider.providedBy(ep))

        try:
            yield ep.listen(NoOpProtocolFactory())
            self.fail("Should have been an exception")
        except RuntimeError as e:
            # make sure we called listenTCP not connectTCP
            self.assertEqual(e, listen)

        repr(self.config.HiddenServices)

    def test_progress_updates(self, ftb):
        config = TorConfig()
        ep = TCPHiddenServiceEndpoint(self.reactor, config, 123)

        self.assertTrue(IProgressProvider.providedBy(ep))
        prog = IProgressProvider(ep)
        ding = Mock()
        prog.add_progress_listener(ding)
        args = (50, "blarg", "Doing that thing we talked about.")
        # kind-of cheating, test-wise?
        ep._tor_progress_update(*args)
        self.assertTrue(ding.called_with(*args))

    def test_progress_updates_private_tor(self, ftb):
        with patch('txtorcon.endpoints.launch_tor') as tor:
            ep = TCPHiddenServiceEndpoint.private_tor(self.reactor, 1234)
            self.assertEqual(len(tor.mock_calls), 1)
            tor.call_args[1]['progress_updates'](40, 'FOO', 'foo to the bar')
            return ep

    def test_progress_updates_system_tor(self, ftb):
        control_ep = Mock()
        control_ep.connect = Mock(return_value=defer.succeed(None))
        directlyProvides(control_ep, IStreamClientEndpoint)
        ep = TCPHiddenServiceEndpoint.system_tor(self.reactor, control_ep, 1234)
        ep._tor_progress_update(40, "FOO", "foo to bar")
        return ep

    def test_progress_updates_global_tor(self, ftb):
        with patch('txtorcon.endpoints.get_global_tor') as tor:
            ep = TCPHiddenServiceEndpoint.global_tor(self.reactor, 1234)
            tor.call_args[1]['progress_updates'](40, 'FOO', 'foo to the bar')
            return ep

    def test_hiddenservice_key_unfound(self, ftb):
        ep = TCPHiddenServiceEndpoint.private_tor(
            self.reactor,
            1234,
            hidden_service_dir='/dev/null'
        )

        # FIXME Mock() should work somehow for this, but I couldn't
        # make it "go"
        class Blam(object):
            @property
            def private_key(self):
                raise IOError("blam")
        ep.hiddenservice = Blam()
        self.assertEqual(ep.onion_private_key, None)
        return ep

    def test_multiple_listen(self, ftb):
        ep = TCPHiddenServiceEndpoint(self.reactor, self.config, 123)
        d0 = ep.listen(NoOpProtocolFactory())

        @defer.inlineCallbacks
        def more_listen(arg):
            yield arg.stopListening()
            d1 = ep.listen(NoOpProtocolFactory())

            def foo(arg):
                return arg
            d1.addBoth(foo)
            defer.returnValue(arg)
            return
        d0.addBoth(more_listen)
        self.config.bootstrap()

        def check(arg):
            self.assertEqual('127.0.0.1', ep.tcp_endpoint._interface)
            self.assertEqual(len(self.config.HiddenServices), 1)
        d0.addCallback(check).addErrback(self.fail)
        return d0

    def test_already_bootstrapped(self, ftb):
        self.config.bootstrap()
        ep = TCPHiddenServiceEndpoint(self.reactor, self.config, 123)
        d = ep.listen(NoOpProtocolFactory())
        return d

    @defer.inlineCallbacks
    def test_explicit_data_dir(self, ftb):
        with util.TempDir() as tmp:
            d = str(tmp)
            with open(os.path.join(d, 'hostname'), 'w') as f:
                f.write('public')

            config = TorConfig(self.protocol)
            ep = TCPHiddenServiceEndpoint(self.reactor, config, 123, d)

            # make sure listen() correctly configures our hidden-serivce
            # with the explicit directory we passed in above
            yield ep.listen(NoOpProtocolFactory())

            self.assertEqual(1, len(config.HiddenServices))
            self.assertEqual(config.HiddenServices[0].dir, d)
            self.assertEqual(config.HiddenServices[0].hostname, 'public')

    def test_failure(self, ftb):
        self.reactor.failures = 1
        ep = TCPHiddenServiceEndpoint(self.reactor, self.config, 123)
        d = ep.listen(NoOpProtocolFactory())
        self.config.bootstrap()
        d.addErrback(self.check_error)
        return d

    def check_error(self, failure):
        self.assertEqual(failure.type, error.CannotListenError)
        return None

    def test_parse_via_plugin(self, ftb):
        # make sure we have a valid thing from get_global_tor without
        # actually launching tor
        config = TorConfig()
        config.post_bootstrap = defer.succeed(config)
        from txtorcon import torconfig
        torconfig._global_tor_config = None
        get_global_tor(
            self.reactor,
            _tor_launcher=lambda react, config, prog: defer.succeed(config)
        )
        ep = serverFromString(
            self.reactor,
            'onion:88:localPort=1234:hiddenServiceDir=/foo/bar'
        )
        self.assertEqual(ep.public_port, 88)
        self.assertEqual(ep.local_port, 1234)
        self.assertEqual(ep.hidden_service_dir, '/foo/bar')

    def test_parse_user_path(self, ftb):
        # this makes sure we expand users and symlinks in
        # hiddenServiceDir args. see Issue #77

        # make sure we have a valid thing from get_global_tor without
        # actually launching tor
        config = TorConfig()
        config.post_bootstrap = defer.succeed(config)
        from txtorcon import torconfig
        torconfig._global_tor_config = None
        get_global_tor(
            self.reactor,
            _tor_launcher=lambda react, config, prog: defer.succeed(config)
        )
        ep = serverFromString(
            self.reactor,
            'onion:88:localPort=1234:hiddenServiceDir=~/blam/blarg'
        )
        # would be nice to have a fixed path here, but then would have
        # to run as a known user :/
        # maybe using the docker stuff to run integration tests better here?
        self.assertEqual(
            os.path.expanduser('~/blam/blarg'),
            ep.hidden_service_dir
        )

    def test_parse_relative_path(self, ftb):
        # this makes sure we convert a relative path to absolute
        # hiddenServiceDir args. see Issue #77

        # make sure we have a valid thing from get_global_tor without
        # actually launching tor
        config = TorConfig()
        config.post_bootstrap = defer.succeed(config)
        from txtorcon import torconfig
        torconfig._global_tor_config = None
        get_global_tor(
            self.reactor,
            _tor_launcher=lambda react, config, prog: defer.succeed(config)
        )

        orig = os.path.realpath('.')
        try:
            with util.TempDir() as t:
                t = str(t)
                os.chdir(t)
                os.mkdir(os.path.join(t, 'foo'))
                hsdir = os.path.join(t, 'foo', 'blam')
                os.mkdir(hsdir)

                ep = serverFromString(
                    self.reactor,
                    'onion:88:localPort=1234:hiddenServiceDir=foo/blam'
                )
                self.assertEqual(
                    os.path.realpath(hsdir),
                    ep.hidden_service_dir
                )

        finally:
            os.chdir(orig)

    @defer.inlineCallbacks
    def test_stealth_auth(self, ftb):
        '''
        make sure we produce a HiddenService instance with stealth-auth
        lines if we had authentication specified in the first place.
        '''

        config = TorConfig(self.protocol)
        ep = TCPHiddenServiceEndpoint(self.reactor, config, 123, '/dev/null',
                                      stealth_auth=['alice', 'bob'])

        # make sure listen() correctly configures our hidden-serivce
        # with the explicit directory we passed in above
        d = ep.listen(NoOpProtocolFactory())

        def foo(fail):
            print("ERROR", fail)
        d.addErrback(foo)
        yield d  # returns 'port'
        self.assertEqual(1, len(config.HiddenServices))
        self.assertEqual(config.HiddenServices[0].dir, '/dev/null')
        self.assertEqual(
            config.HiddenServices[0].authorize_client[0],
            'stealth alice,bob'
        )
        self.assertEqual(None, ep.onion_uri)
        # XXX cheating; private API
        config.HiddenServices[0].hostname = 'oh my'
        self.assertEqual('oh my', ep.onion_uri)

    @defer.inlineCallbacks
    def test_factory(self, ftb):
        reactor = Mock()
        cp = Mock()
        cp.get_conf = Mock(return_value=defer.succeed(dict()))

        with patch(u'txtorcon.endpoints.available_tcp_port', return_value=9999):
            ep = yield TorClientEndpoint.from_connection(reactor, cp, 'localhost', 1234)

        self.assertTrue(isinstance(ep, TorClientEndpoint))
        self.assertEqual(ep.host, 'localhost')
        self.assertEqual(ep.port, 1234)


class EndpointLaunchTests(unittest.TestCase):

    def setUp(self):
        self.reactor = FakeReactorTcp(self)
        self.protocol = FakeControlProtocol([])

    def test_onion_address(self):
        addr = TorOnionAddress("foo.onion", 80)
        # just want to run these and assure they don't throw
        # exceptions.
        repr(addr)
        hash(addr)

    def test_onion_parse_unix_socket(self):
        r = proto_helpers.MemoryReactor()
        serverFromString(r, "onion:80:controlPort=/tmp/foo")

    @patch('txtorcon.TCPHiddenServiceEndpoint.system_tor')
    @patch('txtorcon.TCPHiddenServiceEndpoint.global_tor')
    @patch('txtorcon.TCPHiddenServiceEndpoint.private_tor')
    @defer.inlineCallbacks
    def test_endpoint_launch_tor(self, private_tor, global_tor, system_tor):
        """
        we just want to confirm that calling listen results in the
        spawning of a Tor process; the parsing/setup from string are
        checked elsewhere.
        """

        reactor = proto_helpers.MemoryReactor()
        ep = serverFromString(reactor, 'onion:8888')
        yield ep.listen(NoOpProtocolFactory())
        self.assertEqual(global_tor.call_count, 1)
        self.assertEqual(private_tor.call_count, 0)
        self.assertEqual(system_tor.call_count, 0)

    @patch('txtorcon.TCPHiddenServiceEndpoint.system_tor')
    @patch('txtorcon.TCPHiddenServiceEndpoint.global_tor')
    @patch('txtorcon.TCPHiddenServiceEndpoint.private_tor')
    @defer.inlineCallbacks
    def test_endpoint_connect_tor(self, private_tor, global_tor, system_tor):
        """
        similar to above test, we're confirming that an
        endpoint-string with 'controlPort=xxxx' in it calls the API
        that will connect to a running Tor.
        """

        reactor = proto_helpers.MemoryReactor()
        ep = serverFromString(
            reactor,
            'onion:8888:controlPort=9055:localPort=1234'
        )
        yield ep.listen(NoOpProtocolFactory())
        self.assertEqual(global_tor.call_count, 0)
        self.assertEqual(private_tor.call_count, 0)
        self.assertEqual(system_tor.call_count, 1)

        # unfortunately, we don't add the hidden-service
        # configurations until we've connected to the launched Tor
        # and bootstrapped a TorConfig object -- and that's a ton
        # of stuff to fake out. Most of that is covered by the
        # parsing tests (i.e. are we getting the right config
        # values from a server-endpoint-string)


# FIXME should probably go somewhere else, so other tests can easily use these.
@implementer(IProtocol)
class FakeProtocol(object):

    def dataReceived(self, data):
        print("DATA", data)

    def connectionLost(self, reason):
        print("LOST", reason)

    def makeConnection(self, transport):
        print("MAKE", transport)
        transport.protocol = self

    def connectionMade(self):
        print("MADE!")


@implementer(IAddress)
class FakeAddress(object):

    compareAttributes = ('type', 'host', 'port')
    type = 'fakeTCP'

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __repr__(self):
        return '%s(%r, %d)' % (
            self.__class__.__name__, self.host, self.port)

    def __hash__(self):
        return hash((self.type, self.host, self.port))


@implementer(IListeningPort)
class FakeListeningPort(object):

    def __init__(self, port):
        self.port = port

    def startListening(self):
        self.factory.doStart()

    def stopListening(self):
        self.factory.doStop()

    def getHost(self):
        return FakeAddress('host', self.port)


def port_generator():
    # XXX six has xrange/range stuff?
    for x in range(65535, 0, -1):
        yield x


@implementer(IReactorTCP, IReactorCore)
class FakeReactorTcp(object):

    failures = 0
    _port_generator = port_generator()

    def __init__(self, test):
        self.protocol = TorControlProtocol()
        self.protocol.connectionMade = lambda: None
        self.transport = proto_helpers.StringTransport()
        self.transport.protocol = self.protocol

        def blam():
            self.protocol.outReceived(b"Bootstrap")
        self.transport.closeStdin = blam
        self.protocol.makeConnection(self.transport)
        self.test = test

    def spawnProcess(self, processprotocol, bin, args, env, path,
                     uid=None, gid=None, usePTY=None, childFDs=None):
        self.protocol = processprotocol
        self.protocol.makeConnection(self.transport)
        self.transport.process_protocol = processprotocol
        return self.transport

    def addSystemEventTrigger(self, *args):
        self.test.assertEqual(args[0], 'before')
        self.test.assertEqual(args[1], 'shutdown')
        # we know this is just for the temporary file cleanup, so we
        # nuke it right away to avoid polluting /tmp by calling the
        # callback now.
        args[2]()

    def listenTCP(self, port, factory, **kwargs):
        '''returns IListeningPort'''
        if self.failures > 0:
            self.failures -= 1
            raise error.CannotListenError(None, None, None)

        if port == 0:
            port = next(self._port_generator)
        p = FakeListeningPort(port)
        p.factory = factory
        p.startListening()
        return p

    def connectTCP(self, host, port, factory, timeout, bindAddress):
        '''should return IConnector'''
        r = tcp.Connector(
            host, port, factory, timeout,
            bindAddress, reactor=self
        )

        def blam(*args):
            print("BLAAAAAM", args)
        r.connect = blam
        return r

    def connectUNIX(self, address, factory, timeout=30, checkPID=0):
        '''should return IConnector'''
        r = unix.Connector(
            address, factory, timeout, self, checkPID,
        )

        def blam(*args):
            print("BLAAAAAM", args)
        r.connect = blam
        return r


class FakeTorSocksEndpoint(object):
    """
    This ctor signature matches TorSocksEndpoint even though we don't
    use it in the tests.
    """

    def __init__(self, socks_endpoint, host, port, tls=False, **kw):
        self.host = host
        self.port = port
        self.transport = None

        self.failure = kw.get('failure', None)
        self.accept_port = kw.get('accept_port', None)

    def connect(self, fac):
        self.factory = fac
        if self.accept_port:
            if self.port != self.accept_port:
                return defer.fail(self.failure)
        else:
            if self.failure:
                return defer.fail(self.failure)
        self.proto = fac.buildProtocol(None)
        transport = proto_helpers.StringTransportWithDisconnection()
        self.proto.makeConnection(transport)
        self.transport = transport
        return defer.succeed(self.proto)


class FakeSocksProto(object):
    def __init__(self, host, port, method, factory):
        self.host = host
        self.port = port
        self.method = method
        self.factory = factory
        self._done = SingleObserver()

    def when_done(self):
        return self._done.when_fired()

    def makeConnection(self, transport):
        proto = self.factory.buildProtocol('socks5 addr')
        self._done.fire(proto)


class TestTorCircuitEndpoint(unittest.TestCase):

    @defer.inlineCallbacks
    def test_circuit_failure(self):
        """
        If the circuit fails the error propagates
        """
        reactor = Mock()
        torstate = Mock()
        target = Mock()
        target.connect = Mock(return_value=defer.succeed(None))
        circ = Mock()
        circ.state = 'FAILED'
        src_addr = Mock()
        src_addr.host = 'host'
        src_addr.port = 1234
        target._get_address = Mock(return_value=defer.succeed(src_addr))
        stream = Mock()
        stream.source_port = 1234
        stream.source_addr = 'host'

        # okay, so we fire up our circuit-endpoint with mostly mocked
        # things, and a circuit that's already in 'FAILED' state.
        ep = TorCircuitEndpoint(reactor, torstate, circ, target)

        # should get a Failure from the connect()
        d = ep.connect(Mock())
        attacher = yield _get_circuit_attacher(reactor, Mock())
        attacher.attach_stream(stream, [circ])
        try:
            yield d
            self.fail("Should get exception")
        except RuntimeError as e:
            assert "unusable" in str(e)

    @defer.inlineCallbacks
    def test_circuit_stream_failure(self):
        """
        If the stream-attach fails the error propagates
        """
        reactor = Mock()
        torstate = Mock()
        target = Mock()
        target.connect = Mock(return_value=defer.succeed(None))
        circ = Mock()
        circ.state = 'FAILED'
        src_addr = Mock()
        src_addr.host = 'host'
        src_addr.port = 1234
        target._get_address = Mock(return_value=defer.succeed(src_addr))
        stream = Mock()
        stream.source_port = 1234
        stream.source_addr = 'host'

        # okay, so we fire up our circuit-endpoint with mostly mocked
        # things, and a circuit that's already in 'FAILED' state.
        ep = TorCircuitEndpoint(reactor, torstate, circ, target)

        # should get a Failure from the connect()
        d = ep.connect(Mock())
        attacher = yield _get_circuit_attacher(reactor, Mock())
        attacher.attach_stream_failure(stream, RuntimeError("a bad thing"))
        try:
            yield d
            self.fail("Should get exception")
        except RuntimeError as e:
            self.assertEqual("a bad thing", str(e))

    @defer.inlineCallbacks
    def test_success(self):
        """
        Connect a stream via a circuit
        """
        reactor = Mock()
        torstate = Mock()
        target = Mock()
        target.connect = Mock(return_value=defer.succeed('fake proto'))
        circ = Mock()
        circ.state = 'NEW'
        src_addr = Mock()
        src_addr.host = 'host'
        src_addr.port = 1234
        target._get_address = Mock(return_value=defer.succeed(src_addr))
        stream = Mock()
        stream.source_port = 1234
        stream.source_addr = 'host'

        # okay, so we fire up our circuit-endpoint with mostly mocked
        # things, and a circuit that's already in 'FAILED' state.
        ep = TorCircuitEndpoint(reactor, torstate, circ, target)

        # should get a Failure from the connect()
        d = ep.connect(Mock())
        attacher = yield _get_circuit_attacher(reactor, torstate)
        yield attacher.attach_stream(stream, [circ])
        proto = yield d
        self.assertEqual(proto, 'fake proto')


class TestTorClientEndpoint(unittest.TestCase):

    @patch('txtorcon.endpoints.get_global_tor')
    def test_client_connection_failed(self, ggt):
        """
        This test is equivalent to txsocksx's
        TestSOCKS4ClientEndpoint.test_clientConnectionFailed
        """
        tor_endpoint = FakeTorSocksEndpoint(
            None, "host123", 9050,
            failure=Failure(ConnectionRefusedError()),
        )
        endpoint = TorClientEndpoint(
            '', 0,
            socks_endpoint=tor_endpoint,
        )
        d = endpoint.connect(None)
        return self.assertFailure(d, ConnectionRefusedError)

    def test_client_connection_failed_user_password(self):
        """
        Same as above, but with a username/password.
        """
        tor_endpoint = FakeTorSocksEndpoint(
            None, "fakehose", 9050,
            failure=Failure(ConnectionRefusedError()),
        )
        endpoint = TorClientEndpoint(
            'invalid host', 0,
            socks_username='billy', socks_password='s333cure',
            socks_endpoint=tor_endpoint)
        d = endpoint.connect(None)
        # XXX we haven't fixed socks.py to support user/pw yet ...
        return self.assertFailure(d, RuntimeError)
        return self.assertFailure(d, ConnectionRefusedError)

    def test_no_host(self):
        self.assertRaises(
            ValueError,
            TorClientEndpoint, None, None, Mock(),
        )

    def test_parser_basic(self):
        ep = clientFromString(None, 'tor:host=timaq4ygg2iegci7.onion:port=80:socksPort=9050')

        self.assertEqual(ep.host, 'timaq4ygg2iegci7.onion')
        self.assertEqual(ep.port, 80)
        # XXX what's "the Twisted way" to get the port out here?
        self.assertEqual(ep._socks_endpoint._port, 9050)

    def test_parser_user_password(self):
        epstring = 'tor:host=torproject.org:port=443' + \
                   ':socksUsername=foo:socksPassword=bar'
        ep = clientFromString(None, epstring)

        self.assertEqual(ep.host, 'torproject.org')
        self.assertEqual(ep.port, 443)
        self.assertEqual(ep._socks_username, 'foo')
        self.assertEqual(ep._socks_password, 'bar')

    def test_default_factory(self):
        """
        This test is equivalent to txsocksx's
        TestSOCKS5ClientEndpoint.test_defaultFactory
        """

        tor_endpoint = FakeTorSocksEndpoint(None, "fakehost", 9050)
        endpoint = TorClientEndpoint(
            '', 0,
            socks_endpoint=tor_endpoint,
        )
        endpoint.connect(Mock)
        self.assertEqual(tor_endpoint.transport.value(), b'\x05\x01\x00')

    @defer.inlineCallbacks
    def test_success(self):
        with patch.object(_TorSocksFactory, "protocol", FakeSocksProto):
            tor_endpoint = FakeTorSocksEndpoint(Mock(), "fakehost", 9050)
            endpoint = TorClientEndpoint(
                u'meejah.ca', 443,
                socks_endpoint=tor_endpoint,
            )
            proto = yield endpoint.connect(MagicMock())
            self.assertTrue(isinstance(proto, FakeSocksProto))
            self.assertEqual(u"meejah.ca", proto.host)
            self.assertEqual(443, proto.port)
            self.assertEqual('CONNECT', proto.method)

    def test_good_port_retry(self):
        """
        This tests that our Tor client endpoint retry logic works correctly.
        We create a proxy endpoint that fires a ConnectionRefusedError
        unless the connecting port matches. We attempt to connect with the
        proxy endpoint for each port that the Tor client endpoint will try.
        """
        success_ports = TorClientEndpoint.socks_ports_to_try
        for port in success_ports:
            tor_endpoint = FakeTorSocksEndpoint(
                u"fakehost", "127.0.0.1", port,
                accept_port=port,
                failure=Failure(ConnectionRefusedError()),
            )

            endpoint = TorClientEndpoint(
                '', 0,
                socks_endpoint=tor_endpoint,
            )
            endpoint.connect(Mock())
            self.assertEqual(tor_endpoint.transport.value(), b'\x05\x01\x00')

    def test_bad_port_retry(self):
        """
        This tests failure to connect to the ports on the "try" list.
        """
        fail_ports = [1984, 666]
        for port in fail_ports:
            ep = FakeTorSocksEndpoint(
                '', '', 0,
                accept_port=port,
                failure=Failure(ConnectionRefusedError()),
            )
            endpoint = TorClientEndpoint('', 0, socks_endpoint=ep)
            d = endpoint.connect(None)
            return self.assertFailure(d, ConnectionRefusedError)

    @patch('txtorcon.endpoints.TorSocksEndpoint')
    def test_default_socks_ports_fails(self, ep_mock):
        """
        Ensure we iterate over the default socks ports
        """

        class FakeSocks5(object):

            def __init__(self, *args, **kw):
                pass

            def connect(self, *args, **kw):
                raise ConnectionRefusedError()

            def _get_address(self):
                return defer.succeed(None)

        ep_mock.side_effect = FakeSocks5
        endpoint = TorClientEndpoint('', 0)
        d = endpoint.connect(Mock())
        self.assertFailure(d, ConnectionRefusedError)

    @patch('txtorcon.endpoints.TorSocksEndpoint')
    @defer.inlineCallbacks
    def test_default_socks_ports_happy(self, ep_mock):
        """
        Ensure we iterate over the default socks ports
        """

        proto = object()

        class FakeSocks5(object):

            def __init__(self, *args, **kw):
                pass

            def connect(self, *args, **kw):
                return proto

            def _get_address(self):
                return defer.succeed(None)

        ep_mock.side_effect = FakeSocks5
        endpoint = TorClientEndpoint('', 0)
        p2 = yield endpoint.connect(None)
        self.assertTrue(proto is p2)

    @patch('txtorcon.endpoints.TorSocksEndpoint')
    @defer.inlineCallbacks
    def test_tls_socks_no_endpoint(self, ep_mock):
        the_proto = object()
        proto = defer.succeed(the_proto)

        class FakeSocks5(object):

            def __init__(self, *args, **kw):
                pass

            def connect(self, *args, **kw):
                return proto

            def _get_address(self):
                return defer.succeed(None)

        ep_mock.side_effect = FakeSocks5
        endpoint = TorClientEndpoint('torproject.org', 0, tls=True)
        p2 = yield endpoint.connect(None)
        self.assertTrue(the_proto is p2)

    @patch('txtorcon.endpoints.TorSocksEndpoint')
    @defer.inlineCallbacks
    def test_tls_socks_with_endpoint(self, ep_mock):
        """
        Same as above, except we provide an explicit endpoint
        """
        the_proto = object()
        proto_d = defer.succeed(the_proto)

        class FakeSocks5(object):

            def __init__(self, *args, **kw):
                pass

            def connect(self, *args, **kw):
                return proto_d

            def _get_address(self):
                return defer.succeed(None)

        ep_mock.side_effect = FakeSocks5
        endpoint = TorClientEndpoint(
            u'torproject.org', 0,
            socks_endpoint=clientFromString(Mock(), "tcp:localhost:9050"),
            tls=True,
        )
        p2 = yield endpoint.connect(None)
        self.assertTrue(p2 is the_proto)

    def test_client_endpoint_old_api(self):
        """
        Test the old API of passing socks_host, socks_port
        """

        reactor = Mock()
        endpoint = TorClientEndpoint(
            'torproject.org', 0,
            socks_hostname='localhost',
            socks_port=9050,
            reactor=reactor,
        )
        self.assertTrue(
            isinstance(endpoint._socks_endpoint, TCP4ClientEndpoint)
        )

        endpoint.connect(Mock())
        calls = reactor.mock_calls
        self.assertEqual(1, len(calls))
        name, args, kw = calls[0]
        self.assertEqual("connectTCP", name)
        self.assertEqual("localhost", args[0])
        self.assertEqual(9050, args[1])

    def test_client_endpoint_get_address(self):
        """
        Test the old API of passing socks_host, socks_port
        """

        reactor = Mock()
        endpoint = TorClientEndpoint(
            'torproject.org', 0,
            socks_endpoint=clientFromString(Mock(), "tcp:localhost:9050"),
            reactor=reactor,
        )
        d = endpoint._get_address()
        self.assertTrue(not d.called)


class TestSocksFactory(unittest.TestCase):

    @defer.inlineCallbacks
    def test_explicit_socks(self):
        reactor = Mock()
        cp = Mock()
        cp.get_conf = Mock(
            return_value=defer.succeed({
                'SocksPort': ['9050', '9150', 'unix:/tmp/boom']
            })
        )

        ep = yield _create_socks_endpoint(reactor, cp, socks_config='unix:/tmp/boom')

        self.assertTrue(isinstance(ep, UNIXClientEndpoint))

    @defer.inlineCallbacks
    def test_unix_socket_with_options(self):
        reactor = Mock()
        cp = Mock()
        cp.get_conf = Mock(
            return_value=defer.succeed({
                'SocksPort': ['unix:/tmp/boom SomeOption']
            })
        )

        ep = yield _create_socks_endpoint(reactor, cp)

        self.assertTrue(isinstance(ep, UNIXClientEndpoint))
        self.assertEqual("/tmp/boom", ep._path)

    @defer.inlineCallbacks
    def test_nothing_exists(self):
        reactor = Mock()
        cp = Mock()
        cp.get_conf = Mock(return_value=defer.succeed(dict()))

        with patch(u'txtorcon.endpoints.available_tcp_port', return_value=9999):
            ep = yield _create_socks_endpoint(reactor, cp)

        self.assertTrue(isinstance(ep, TCP4ClientEndpoint))
        # internal details, but ...
        self.assertEqual(ep._port, 9999)
