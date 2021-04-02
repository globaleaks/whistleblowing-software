from __future__ import print_function

from zope.interface import implementer, directlyProvides
from zope.interface.verify import verifyClass
from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.python.failure import Failure
from twisted.internet import task, defer
from twisted.internet.interfaces import IStreamClientEndpoint, IReactorCore

import tempfile
import six

from ipaddress import IPv4Address

from mock import patch, Mock

from txtorcon import TorControlProtocol
from txtorcon import TorProtocolError
from txtorcon import TorState
from txtorcon import Stream
from txtorcon import Circuit
from txtorcon import build_tor_connection
from txtorcon import build_local_tor_connection
from txtorcon import build_timeout_circuit
from txtorcon import CircuitBuildTimedOutError
from txtorcon.interface import IStreamAttacher
from txtorcon.interface import ICircuitListener
from txtorcon.interface import IStreamListener
from txtorcon.interface import StreamListenerMixin
from txtorcon.interface import CircuitListenerMixin
from txtorcon.torstate import _extract_reason
from txtorcon.circuit import _get_circuit_attacher

if six.PY3:
    from .py3_torstate import TorStatePy3Tests  # noqa


@implementer(ICircuitListener)
class CircuitListener(object):

    def __init__(self, expected):
        "expect is a list of tuples: (event, {key:value, key1:value1, ..})"
        self.expected = expected

    def checker(self, state, circuit, arg=None):
        if self.expected[0][0] != state:
            raise RuntimeError(
                'Expected event "%s" not "%s".' %
                (self.expected[0][0], state)
            )
        for (k, v) in self.expected[0][1].items():
            if k == 'arg':
                if v != arg:
                    raise RuntimeError(
                        'Expected argument to have value "%s", not "%s"' % (arg, v)
                    )
            elif getattr(circuit, k) != v:
                raise RuntimeError(
                    'Expected attribute "%s" to have value "%s", not "%s"' %
                    (k, v, getattr(circuit, k))
                )
        self.expected = self.expected[1:]

    def circuit_new(self, circuit):
        self.checker('new', circuit)

    def circuit_launched(self, circuit):
        self.checker('launched', circuit)

    def circuit_extend(self, circuit, router):
        self.checker('extend', circuit, router)

    def circuit_built(self, circuit):
        self.checker('built', circuit)

    def circuit_closed(self, circuit, **kw):
        self.checker('closed', circuit, **kw)

    def circuit_failed(self, circuit, **kw):
        self.checker('failed', circuit, **kw)


@implementer(IStreamListener)
class StreamListener(object):

    def __init__(self, expected):
        "expect is a list of tuples: (event, {key:value, key1:value1, ..})"
        self.expected = expected

    def checker(self, state, stream, arg=None):
        if self.expected[0][0] != state:
            raise RuntimeError(
                'Expected event "%s" not "%s".' % (self.expected[0][0], state)
            )
        for (k, v) in self.expected[0][1].items():
            if k == 'arg':
                if v != arg:
                    raise RuntimeError(
                        'Expected argument to have value "%s", not "%s"' %
                        (arg, v)
                    )
            elif getattr(stream, k) != v:
                raise RuntimeError(
                    'Expected attribute "%s" to have value "%s", not "%s"' %
                    (k, v, getattr(stream, k))
                )
        self.expected = self.expected[1:]

    def stream_new(self, stream):
        self.checker('new', stream)

    def stream_succeeded(self, stream):
        self.checker('succeeded', stream)

    def stream_attach(self, stream, circuit):
        self.checker('attach', stream, circuit)

    def stream_closed(self, stream):
        self.checker('closed', stream)

    def stream_failed(self, stream, reason, remote_reason):
        self.checker('failed', stream, reason)


@implementer(IReactorCore)
class FakeReactor:

    def __init__(self, test):
        self.test = test

    def addSystemEventTrigger(self, *args):
        self.test.assertEqual(args[0], 'before')
        self.test.assertEqual(args[1], 'shutdown')
        self.test.assertEqual(args[2], self.test.state.undo_attacher)
        return 1

    def removeSystemEventTrigger(self, id):
        self.test.assertEqual(id, 1)

    def connectTCP(self, *args, **kw):
        """for testing build_tor_connection"""
        raise RuntimeError('connectTCP: ' + str(args))

    def connectUNIX(self, *args, **kw):
        """for testing build_tor_connection"""
        raise RuntimeError('connectUNIX: ' + str(args))


class FakeCircuit(Circuit):

    def __init__(self, id=-999):
        self.streams = []
        self.id = id
        self.state = 'BOGUS'


@implementer(IStreamClientEndpoint)
class FakeEndpoint:

    def get_info_raw(self, keys):
        ans = '\r\n'.join(map(lambda k: '%s=' % k, keys.split()))
        return defer.succeed(ans)

    def get_info_incremental(self, key, linecb):
        linecb('%s=' % key)
        return defer.succeed('')

    def connect(self, protocol_factory):
        self.proto = TorControlProtocol()
        self.proto.transport = proto_helpers.StringTransport()
        self.proto.get_info_raw = self.get_info_raw
        self.proto.get_info_incremental = self.get_info_incremental
        self.proto._set_valid_events(
            'GUARD STREAM CIRC NS NEWCONSENSUS ORCONN NEWDESC ADDRMAP STATUS_GENERAL'
        )

        return defer.succeed(self.proto)


@implementer(IStreamClientEndpoint)
class FakeEndpointAnswers:

    def __init__(self, answers):
        self.answers = answers
        # since we use pop() we need these to be "backwards"
        self.answers.reverse()

    def get_info_raw(self, keys):
        ans = ''
        for k in keys.split():
            if len(self.answers) == 0:
                raise TorProtocolError(551, "ran out of answers")
            ans += '%s=%s\r\n' % (k, self.answers.pop())
        return ans[:-2]                 # don't want trailing \r\n

    def get_info_incremental(self, key, linecb):
        data = self.answers.pop().split('\n')
        if len(data) == 1:
            linecb('{}={}'.format(key, data[0]))
        else:
            linecb('{}='.format(key))
            for line in data:
                linecb(line)
        return defer.succeed('')

    def connect(self, protocol_factory):
        self.proto = TorControlProtocol()
        self.proto.transport = proto_helpers.StringTransport()
        self.proto.get_info_raw = self.get_info_raw
        self.proto.get_info_incremental = self.get_info_incremental
        self.proto._set_valid_events(
            'GUARD STREAM CIRC NS NEWCONSENSUS ORCONN NEWDESC ADDRMAP STATUS_GENERAL'
        )

        return defer.succeed(self.proto)


class BootstrapTests(unittest.TestCase):

    def confirm_proto(self, x):
        self.assertTrue(isinstance(x, TorControlProtocol))
        self.assertTrue(x.post_bootstrap.called)
        return x

    def confirm_state(self, x):
        self.assertIsInstance(x, TorState)
        self.assertTrue(x.post_bootstrap.called)
        return x

    def confirm_consensus(self, x):
        self.assertEqual(1, len(x.all_routers))
        self.assertEqual('fake', list(x.routers.values())[0].name)
        return x

    def test_build(self):
        p = FakeEndpoint()
        d = build_tor_connection(p, build_state=False)
        d.addCallback(self.confirm_proto)
        p.proto.post_bootstrap.callback(p.proto)
        return d

    def test_build_tcp(self):
        d = build_tor_connection((FakeReactor(self), '127.0.0.1', 1234))
        d.addCallback(self.fail)
        d.addErrback(lambda x: None)
        return d

    def test_build_unix(self):
        tf = tempfile.NamedTemporaryFile()
        d = build_tor_connection((FakeReactor(self), tf.name))
        d.addCallback(self.fail)
        d.addErrback(lambda x: None)
        return d

    def test_build_unix_wrong_permissions(self):
        self.assertRaises(
            ValueError,
            build_tor_connection,
            (FakeReactor(self), 'a non-existant filename')
        )

    def test_build_wrong_size_tuple(self):
        self.assertRaises(TypeError, build_tor_connection, (1, 2, 3, 4))

    def test_build_wrong_args_entirely(self):
        self.assertRaises(
            TypeError,
            build_tor_connection,
            'incorrect argument'
        )

    def confirm_pid(self, state):
        self.assertEqual(state.tor_pid, 1234)
        return state

    def confirm_no_pid(self, state):
        self.assertEqual(state.tor_pid, 0)

    def test_build_with_answers(self):
        p = FakeEndpointAnswers(['',     # ns/all
                                 '',     # circuit-status
                                 '',     # stream-status
                                 '',     # address-mappings/all
                                 '',     # entry-guards
                                 '1234'  # PID
                                 ])

        d = build_tor_connection(p, build_state=True)
        d.addCallback(self.confirm_state).addErrback(self.fail)
        d.addCallback(self.confirm_pid).addErrback(self.fail)
        p.proto.post_bootstrap.callback(p.proto)
        return d

    def test_build_with_answers_ns(self):
        fake_consensus = '\n'.join([
            'r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 11.11.11.11 443 80',
            's Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof',
            'r ekaf foooooooooooooooooooooooooo barbarbarbarbarbarbarbarbar 2011-11-11 16:30:00 22.22.22.22 443 80',
            's Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof',
            '',
        ])
        p = FakeEndpointAnswers([fake_consensus,     # ns/all
                                 '',     # circuit-status
                                 '',     # stream-status
                                 '',     # address-mappings/all
                                 '',     # entry-guards
                                 '1234'  # PID
                                 ])

        d = build_tor_connection(p, build_state=True)
        d.addCallback(self.confirm_state).addErrback(self.fail)
        d.addCallback(self.confirm_pid).addErrback(self.fail)
        d.addCallback(self.confirm_consensus).addErrback(self.fail)
        p.proto.post_bootstrap.callback(p.proto)
        return d

    def test_build_with_answers_no_pid(self):
        p = FakeEndpointAnswers(['',    # ns/all
                                 '',    # circuit-status
                                 '',    # stream-status
                                 '',    # address-mappings/all
                                 ''     # entry-guards
                                 ])

        d = build_tor_connection(p, build_state=True)
        d.addCallback(self.confirm_state)
        d.addCallback(self.confirm_no_pid)
        p.proto.post_bootstrap.callback(p.proto)
        return d

    def test_build_with_answers_guards_unfound_entry(self):
        p = FakeEndpointAnswers(['',    # ns/all
                                 '',    # circuit-status
                                 '',    # stream-status
                                 '',    # address-mappings/all
                                 '\n\nkerblam up\nOK\n'     # entry-guards
                                 ])

        d = build_tor_connection(p, build_state=True)
        d.addCallback(self.confirm_state)
        d.addCallback(self.confirm_no_pid)
        p.proto.post_bootstrap.callback(p.proto)
        return d

    def test_build_local_unix(self):
        reactor = FakeReactor(self)
        d = build_local_tor_connection(reactor)
        d.addErrback(lambda _: None)
        return d

    def test_build_local_tcp(self):
        reactor = FakeReactor(self)
        d = build_local_tor_connection(reactor, socket=None)
        d.addErrback(lambda _: None)
        return d


class UtilTests(unittest.TestCase):

    def test_extract_reason_no_reason(self):
        reason = _extract_reason(dict())
        self.assertEqual("unknown", reason)


class StateTests(unittest.TestCase):

    def setUp(self):
        self.protocol = TorControlProtocol()
        self.state = TorState(self.protocol)
        # avoid spew in trial logs; state prints this by default
        self.state._attacher_error = lambda f: f
        self.protocol.connectionMade = lambda: None
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)

    def test_close_stream_with_attacher(self):
        @implementer(IStreamAttacher)
        class MyAttacher(object):

            def __init__(self):
                self.streams = []

            def attach_stream(self, stream, circuits):
                self.streams.append(stream)
                return None

        attacher = MyAttacher()
        self.state.set_attacher(attacher, FakeReactor(self))
        self.state._stream_update("76 CLOSED 0 www.example.com:0 REASON=DONE")

    def test_attacher_error_handler(self):
        # make sure error-handling "does something" that isn't blowing up
        with patch('sys.stdout'):
            TorState(self.protocol)._attacher_error(Failure(RuntimeError("quote")))

    def test_stream_update(self):
        # we use a circuit ID of 0 so it doesn't try to look anything
        # up but it's not really correct to have a SUCCEEDED w/o a
        # valid circuit, I don't think
        self.state._stream_update('1610 SUCCEEDED 0 74.125.224.243:80')
        self.assertTrue(1610 in self.state.streams)

    def test_single_streams(self):
        self.state.circuits[496] = FakeCircuit(496)
        self.state._stream_status(
            'stream-status=123 SUCCEEDED 496 www.example.com:6667'
        )
        self.assertEqual(len(self.state.streams), 1)

    def test_multiple_streams(self):
        self.state.circuits[496] = FakeCircuit(496)
        self.state._stream_status(
            '\r\n'.join([
                'stream-status=',
                '123 SUCCEEDED 496 www.example.com:6667',
                '124 SUCCEEDED 496 www.example.com:6667',
            ])
        )
        self.assertEqual(len(self.state.streams), 2)

    def send(self, line):
        self.protocol.dataReceived(line.strip() + b"\r\n")

    @defer.inlineCallbacks
    def test_bootstrap_callback(self):
        '''
        FIXME: something is still screwy with this; try throwing an
        exception from TorState.bootstrap and we'll just hang...
        '''

        from .test_torconfig import FakeControlProtocol
        protocol = FakeControlProtocol(
            [
                "ns/all=",  # ns/all
                "",  # circuit-status
                "",  # stream-status
                "",  # address-mappings/all
                "entry-guards=\r\n$0000000000000000000000000000000000000000=name up\r\n$1111111111111111111111111111111111111111=foo up\r\n$9999999999999999999999999999999999999999=eman unusable 2012-01-01 22:00:00\r\n",  # entry-guards
                "99999",  # process/pid
                "??",  # ip-to-country/0.0.0.0
            ]
        )

        state = yield TorState.from_protocol(protocol)

        self.assertEqual(len(state.entry_guards), 2)
        self.assertTrue('$0000000000000000000000000000000000000000' in state.entry_guards)
        self.assertTrue('$1111111111111111111111111111111111111111' in state.entry_guards)
        self.assertEqual(len(state.unusable_entry_guards), 1)
        self.assertTrue('$9999999999999999999999999999999999999999' in state.unusable_entry_guards[0])

    def test_bootstrap_existing_addresses(self):
        '''
        FIXME: something is still screwy with this; try throwing an
        exception from TorState.bootstrap and we'll just hang...
        '''

        d = self.state.post_bootstrap

        clock = task.Clock()
        self.state.addrmap.scheduler = clock

        self.protocol._set_valid_events(' '.join(self.state.event_map.keys()))
        self.state._bootstrap()

        self.send(b"250+ns/all=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250+circuit-status=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250-stream-status=")
        self.send(b"250 OK")

        self.send(b"250+address-mappings/all=")
        self.send(b'www.example.com 127.0.0.1 "2012-01-01 00:00:00"')
        self.send(b'subdomain.example.com 10.0.0.0 "2012-01-01 00:01:02"')
        self.send(b".")
        self.send(b"250 OK")

        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.send(b"250-entry-guards=")
        self.send(b"250 OK")

        self.send(b"250 OK")

        self.assertEqual(len(self.state.addrmap.addr), 4)
        self.assertTrue('www.example.com' in self.state.addrmap.addr)
        self.assertTrue('subdomain.example.com' in self.state.addrmap.addr)
        self.assertTrue('10.0.0.0' in self.state.addrmap.addr)
        self.assertTrue('127.0.0.1' in self.state.addrmap.addr)
        self.assertEqual(IPv4Address(u'127.0.0.1'), self.state.addrmap.find('www.example.com').ip)
        self.assertEqual('www.example.com', self.state.addrmap.find('127.0.0.1').name)
        self.assertEqual(IPv4Address(u'10.0.0.0'), self.state.addrmap.find('subdomain.example.com').ip)
        self.assertEqual('subdomain.example.com', self.state.addrmap.find('10.0.0.0').name)

        return d

    def test_bootstrap_single_existing_circuit(self):
        '''
        test with exactly one circuit. should probably test with 2 as
        well, since there was a bug with the handling of just one.
        '''

        d = self.state.post_bootstrap

        clock = task.Clock()
        self.state.addrmap.scheduler = clock

        self.protocol._set_valid_events(' '.join(self.state.event_map.keys()))
        self.state._bootstrap()

        self.send(b"250+ns/all=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250-circuit-status=123 BUILT PURPOSE=GENERAL")
        self.send(b"250 OK")

        self.send(b"250-stream-status=")
        self.send(b"250 OK")

        self.send(b"250+address-mappings/all=")
        self.send(b".")
        self.send(b"250 OK")

        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.send(b"250-entry-guards=")
        self.send(b"250 OK")

        self.send(b"250 OK")

        self.assertTrue(self.state.find_circuit(123))
        self.assertEqual(len(self.state.circuits), 1)

        return d

    def test_unset_attacher(self):

        @implementer(IStreamAttacher)
        class MyAttacher(object):

            def attach_stream(self, stream, circuits):
                return None

        fr = FakeReactor(self)
        attacher = MyAttacher()
        self.state.set_attacher(attacher, fr)
        self.send(b"250 OK")
        self.state.set_attacher(None, fr)
        self.send(b"250 OK")
        self.assertEqual(
            self.transport.value(),
            b'SETCONF __LeaveStreamsUnattached=1\r\nSETCONF'
            b' __LeaveStreamsUnattached=0\r\n'
        )

    def test_attacher_twice(self):
        """
        It should be an error to set an attacher twice
        """
        @implementer(IStreamAttacher)
        class MyAttacher(object):
            pass

        attacher = MyAttacher()
        self.state.set_attacher(attacher, FakeReactor(self))
        # attach the *same* instance twice; not an error
        self.state.set_attacher(attacher, FakeReactor(self))
        with self.assertRaises(RuntimeError) as ctx:
            self.state.set_attacher(MyAttacher(), FakeReactor(self))
        self.assertTrue(
            "already have an attacher" in str(ctx.exception)
        )

    @defer.inlineCallbacks
    def _test_attacher_both_apis(self):
        """
        similar to above, but first set_attacher is implicit via
        Circuit.stream_via
        """
        reactor = Mock()
        directlyProvides(reactor, IReactorCore)

        @implementer(IStreamAttacher)
        class MyAttacher(object):
            pass

        circ = Circuit(self.state)
        circ.state = 'BUILT'

        # use the "preferred" API, which will set an attacher
        factory = Mock()
        proto = Mock()
        proto.when_done = Mock(return_value=defer.succeed(None))
        factory.connect = Mock(return_value=defer.succeed(proto))
        ep = circ.stream_via(reactor, 'meejah.ca', 443, factory)
        addr = Mock()
        addr.host = '10.0.0.1'
        addr.port = 1011
        ep._target_endpoint._get_address = Mock(return_value=defer.succeed(addr))
        print("EP", ep)
        attacher = yield _get_circuit_attacher(reactor, self.state)
        print("attacher", attacher)
        d = ep.connect('foo')
        print("doin' it")
        stream = Mock()
        import ipaddress
        stream.source_addr = ipaddress.IPv4Address(u'10.0.0.1')
        stream.source_port = 1011
        attacher.attach_stream(stream, [])
        yield d

        # ...now use the low-level API (should be an error)
        with self.assertRaises(RuntimeError) as ctx:
            self.state.set_attacher(MyAttacher(), FakeReactor(self))
        self.assertTrue(
            "already have an attacher" in str(ctx.exception)
        )

    def test_attacher(self):
        @implementer(IStreamAttacher)
        class MyAttacher(object):

            def __init__(self):
                self.streams = []
                self.answer = None

            def attach_stream(self, stream, circuits):
                self.streams.append(stream)
                return self.answer

        attacher = MyAttacher()
        self.state.set_attacher(attacher, FakeReactor(self))
        events = 'GUARD STREAM CIRC NS NEWCONSENSUS ORCONN NEWDESC ADDRMAP STATUS_GENERAL'
        self.protocol._set_valid_events(events)
        self.state._add_events()
        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.send(b"650 STREAM 1 NEW 0 ca.yahoo.com:80 SOURCE_ADDR=127.0.0.1:54327 PURPOSE=USER")
        self.send(b"650 STREAM 1 REMAP 0 87.248.112.181:80 SOURCE=CACHE")
        self.assertEqual(len(attacher.streams), 1)
        self.assertEqual(attacher.streams[0].id, 1)
        self.assertEqual(len(self.protocol.commands), 1)
        self.assertEqual(self.protocol.commands[0][1], b'ATTACHSTREAM 1 0')

        # we should totally ignore .exit URIs
        attacher.streams = []
        self.send(b"650 STREAM 2 NEW 0 10.0.0.0.$E11D2B2269CC25E67CA6C9FB5843497539A74FD0.exit:80 SOURCE_ADDR=127.0.0.1:12345 PURPOSE=TIME")
        self.assertEqual(len(attacher.streams), 0)
        self.assertEqual(len(self.protocol.commands), 1)

        # we should NOT ignore .onion URIs
        attacher.streams = []
        self.send(b"650 STREAM 3 NEW 0 xxxxxxxxxxxxxxxx.onion:80 SOURCE_ADDR=127.0.0.1:12345 PURPOSE=TIME")
        self.assertEqual(len(attacher.streams), 1)
        self.assertEqual(len(self.protocol.commands), 2)
        self.assertEqual(self.protocol.commands[1][1], b'ATTACHSTREAM 3 0')

        # normal attach
        circ = FakeCircuit(1)
        circ.state = 'BUILT'
        self.state.circuits[1] = circ
        attacher.answer = circ
        self.send(b"650 STREAM 4 NEW 0 xxxxxxxxxxxxxxxx.onion:80 SOURCE_ADDR=127.0.0.1:12345 PURPOSE=TIME")
        self.assertEqual(len(attacher.streams), 2)
        self.assertEqual(len(self.protocol.commands), 3)
        self.assertEqual(self.protocol.commands[2][1], b'ATTACHSTREAM 4 1')

    def test_attacher_defer(self):
        @implementer(IStreamAttacher)
        class MyAttacher(object):

            def __init__(self, answer):
                self.streams = []
                self.answer = answer

            def attach_stream(self, stream, circuits):
                self.streams.append(stream)
                return defer.succeed(self.answer)

        self.state.circuits[1] = FakeCircuit(1)
        self.state.circuits[1].state = 'BUILT'
        attacher = MyAttacher(self.state.circuits[1])
        self.state.set_attacher(attacher, FakeReactor(self))

        # boilerplate to finish enough set-up in the protocol so it
        # works
        events = 'GUARD STREAM CIRC NS NEWCONSENSUS ORCONN NEWDESC ADDRMAP STATUS_GENERAL'
        self.protocol._set_valid_events(events)
        self.state._add_events()
        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.send(b"650 STREAM 1 NEW 0 ca.yahoo.com:80 SOURCE_ADDR=127.0.0.1:54327 PURPOSE=USER")
        self.send(b"650 STREAM 1 REMAP 0 87.248.112.181:80 SOURCE=CACHE")
        self.assertEqual(len(attacher.streams), 1)
        self.assertEqual(attacher.streams[0].id, 1)
        self.assertEqual(len(self.protocol.commands), 1)
        self.assertEqual(self.protocol.commands[0][1], b'ATTACHSTREAM 1 1')

    @defer.inlineCallbacks
    def test_attacher_errors(self):
        @implementer(IStreamAttacher)
        class MyAttacher(object):

            def __init__(self, answer):
                self.streams = []
                self.answer = answer

            def attach_stream(self, stream, circuits):
                return self.answer

        self.state.circuits[1] = FakeCircuit(1)
        attacher = MyAttacher(FakeCircuit(2))
        self.state.set_attacher(attacher, FakeReactor(self))

        stream = Stream(self.state)
        stream.id = 3
        msg = ''
        try:
            yield self.state._maybe_attach(stream)
        except Exception as e:
            msg = str(e)
        self.assertTrue('circuit unknown' in msg)

        attacher.answer = self.state.circuits[1]
        msg = ''
        try:
            yield self.state._maybe_attach(stream)
        except Exception as e:
            msg = str(e)
        self.assertTrue('only attach to BUILT' in msg)

        attacher.answer = 'not a Circuit instance'
        msg = ''
        try:
            yield self.state._maybe_attach(stream)
        except Exception as e:
            msg = str(e)
        self.assertTrue('Circuit instance' in msg)

    def test_attacher_no_attach(self):
        @implementer(IStreamAttacher)
        class MyAttacher(object):

            def __init__(self):
                self.streams = []

            def attach_stream(self, stream, circuits):
                self.streams.append(stream)
                return TorState.DO_NOT_ATTACH

        attacher = MyAttacher()
        self.state.set_attacher(attacher, FakeReactor(self))
        events = 'GUARD STREAM CIRC NS NEWCONSENSUS ORCONN NEWDESC ADDRMAP STATUS_GENERAL'
        self.protocol._set_valid_events(events)
        self.state._add_events()
        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.transport.clear()
        self.send(b"650 STREAM 1 NEW 0 ca.yahoo.com:80 SOURCE_ADDR=127.0.0.1:54327 PURPOSE=USER")
        self.send(b"650 STREAM 1 REMAP 0 87.248.112.181:80 SOURCE=CACHE")
        self.assertEqual(len(attacher.streams), 1)
        self.assertEqual(attacher.streams[0].id, 1)
        self.assertEqual(self.transport.value(), b'')

    def test_close_stream_with_id(self):
        stream = Stream(self.state)
        stream.id = 1

        self.state.streams[1] = stream
        self.state.close_stream(stream)
        self.assertEqual(self.transport.value(), b'CLOSESTREAM 1 1\r\n')

    def test_close_stream_with_stream(self):
        stream = Stream(self.state)
        stream.id = 1

        self.state.streams[1] = stream
        self.state.close_stream(stream.id)
        self.assertEqual(self.transport.value(), b'CLOSESTREAM 1 1\r\n')

    def test_close_stream_invalid_reason(self):
        stream = Stream(self.state)
        stream.id = 1
        self.state.streams[1] = stream
        self.assertRaises(
            ValueError,
            self.state.close_stream,
            stream,
            'FOO_INVALID_REASON'
        )

    def test_close_circuit_with_id(self):
        circuit = Circuit(self.state)
        circuit.id = 1

        self.state.circuits[1] = circuit
        self.state.close_circuit(circuit.id)
        self.assertEqual(self.transport.value(), b'CLOSECIRCUIT 1\r\n')

    def test_close_circuit_with_circuit(self):
        circuit = Circuit(self.state)
        circuit.id = 1

        self.state.circuits[1] = circuit
        self.state.close_circuit(circuit)
        self.assertEqual(self.transport.value(), b'CLOSECIRCUIT 1\r\n')

    def test_close_circuit_with_flags(self):
        circuit = Circuit(self.state)
        circuit.id = 1
        # try:
        #     self.state.close_circuit(circuit.id, IfUnused=True)
        #     self.assertTrue(False)
        # except KeyError:
        #     pass

        self.state.circuits[1] = circuit
        self.state.close_circuit(circuit.id, IfUnused=True)
        self.assertEqual(self.transport.value(), b'CLOSECIRCUIT 1 IfUnused\r\n')

    def test_circuit_destroy(self):
        self.state._circuit_update('365 LAUNCHED PURPOSE=GENERAL')
        self.assertTrue(365 in self.state.circuits)
        self.state._circuit_update('365 FAILED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=TIMEOUT')
        self.assertTrue(365 not in self.state.circuits)

    def test_circuit_destroy_already(self):
        self.state._circuit_update('365 LAUNCHED PURPOSE=GENERAL')
        self.assertTrue(365 in self.state.circuits)
        self.state._circuit_update('365 CLOSED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=TIMEOUT')
        self.assertTrue(365 not in self.state.circuits)
        self.state._circuit_update('365 CLOSED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=TIMEOUT')
        self.assertTrue(365 not in self.state.circuits)

    def test_circuit_listener(self):
        events = 'CIRC STREAM ORCONN BW DEBUG INFO NOTICE WARN ERR NEWDESC ADDRMAP AUTHDIR_NEWDESCS DESCCHANGED NS STATUS_GENERAL STATUS_CLIENT STATUS_SERVER GUARD STREAM_BW CLIENTS_SEEN NEWCONSENSUS BUILDTIMEOUT_SET'
        self.protocol._set_valid_events(events)
        self.state._add_events()
        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        # we use this router later on in an EXTEND
        self.state._update_network_status("""ns/all=
r PPrivCom012 2CGDscCeHXeV/y1xFrq1EGqj5g4 QX7NVLwx7pwCuk6s8sxB4rdaCKI 2011-12-20 08:34:19 84.19.178.6 9001 0
s Fast Guard Running Stable Unnamed Valid
w Bandwidth=51500
p reject 1-65535""")

        expected = [('new', {'id': 456}),
                    ('launched', {}),
                    ('extend', {'id': 123})
                    ]
        listen = CircuitListener(expected)
        # first add a Circuit before we listen
        self.protocol.dataReceived(b"650 CIRC 123 LAUNCHED PURPOSE=GENERAL\r\n")
        self.assertEqual(len(self.state.circuits), 1)

        # make sure we get added to existing circuits
        self.state.add_circuit_listener(listen)
        first_circuit = list(self.state.circuits.values())[0]
        self.assertTrue(listen in first_circuit.listeners)

        # now add a Circuit after we started listening
        self.protocol.dataReceived(b"650 CIRC 456 LAUNCHED PURPOSE=GENERAL\r\n")
        self.assertEqual(len(self.state.circuits), 2)
        self.assertTrue(listen in list(self.state.circuits.values())[0].listeners)
        self.assertTrue(listen in list(self.state.circuits.values())[1].listeners)

        # now update the first Circuit to ensure we're really, really
        # listening
        self.protocol.dataReceived(b"650 CIRC 123 EXTENDED $D82183B1C09E1D7795FF2D7116BAB5106AA3E60E~PPrivCom012 PURPOSE=GENERAL\r\n")
        self.assertEqual(len(listen.expected), 0)

    def test_router_from_id_invalid_key(self):
        self.failUnlessRaises(KeyError, self.state.router_from_id, 'somethingcompletelydifferent..thatis42long')

    def test_router_from_named_router(self):
        r = self.state.router_from_id('$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=foo')
        self.assertEqual(r.id_hex, '$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        self.assertEqual(r.unique_name, 'foo')

    def confirm_router_state(self, x):
        self.assertTrue('$624926802351575FF7E4E3D60EFA3BFB56E67E8A' in self.state.routers)
        router = self.state.routers['$624926802351575FF7E4E3D60EFA3BFB56E67E8A']
        self.assertTrue('exit' in router.flags)
        self.assertTrue('fast' in router.flags)
        self.assertTrue('guard' in router.flags)
        self.assertTrue('hsdir' in router.flags)
        self.assertTrue('named' in router.flags)
        self.assertTrue('running' in router.flags)
        self.assertTrue('stable' in router.flags)
        self.assertTrue('v2dir' in router.flags)
        self.assertTrue('valid' in router.flags)
        self.assertTrue('futureproof' in router.flags)
        self.assertEqual(router.bandwidth, 518000)
        self.assertTrue(router.accepts_port(43))
        self.assertTrue(router.accepts_port(53))
        self.assertTrue(not router.accepts_port(44))
        self.assertTrue(router.accepts_port(989))
        self.assertTrue(router.accepts_port(990))
        self.assertTrue(not router.accepts_port(991))
        self.assertTrue(not router.accepts_port(988))

    def test_router_with_ipv6_address(self):
        self.state._update_network_status("""ns/all=
r PPrivCom012 2CGDscCeHXeV/y1xFrq1EGqj5g4 QX7NVLwx7pwCuk6s8sxB4rdaCKI 2011-12-20 08:34:19 84.19.178.6 9001 0
a [2001:0:0:0::0]:4321
s Fast Guard Running Stable Named Valid
w Bandwidth=51500
p reject 1-65535""")
        self.assertEqual(len(self.state.routers_by_name['PPrivCom012'][0].ip_v6), 1)
        self.assertEqual(self.state.routers_by_name['PPrivCom012'][0].ip_v6[0], '[2001:0:0:0::0]:4321')

    def test_invalid_routers(self):
        try:
            self.state._update_network_status('''ns/all=
r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof
w Bandwidth=518000
p accept 43,53,79-81,110,143,194,220,443,953,989-990,993,995,1194,1293,1723,1863,2082-2083,2086-2087,2095-2096,3128,4321,5050,5190,5222-5223,6679,6697,7771,8000,8008,8080-8081,8090,8118,8123,8181,8300,8443,8888
.''')
            self.fail()

        except RuntimeError as e:
            # self.assertTrue('Illegal state' in str(e))
            # flip back when we go back to Automat
            self.assertTrue('Expected "s "' in str(e))

    def test_routers_no_policy(self):
        """
        ensure we can parse a router descriptor which has no p line
        """

        self.state._update_network_status('''ns/all=
r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof
w Bandwidth=518000
r PPrivCom012 2CGDscCeHXeV/y1xFrq1EGqj5g4 QX7NVLwx7pwCuk6s8sxB4rdaCKI 2011-12-20 08:34:19 84.19.178.6 9001 0
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof
w Bandwidth=518000
p accept 43,53,79-81,110,143,194,220,443,953,989-990,993,995,1194,1293,1723,1863,2082-2083,2086-2087,2095-2096,3128,4321,5050,5190,5222-5223,6679,6697,7771,8000,8008,8080-8081,8090,8118,8123,8181,8300,8443,8888
.''')
        self.assertTrue('fake' in self.state.routers.keys())
        self.assertTrue('PPrivCom012' in self.state.routers.keys())

    def test_routers_no_bandwidth(self):
        """
        ensure we can parse a router descriptor which has no w line
        """

        self.state._update_network_status('''ns/all=
r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof
r PPrivCom012 2CGDscCeHXeV/y1xFrq1EGqj5g4 QX7NVLwx7pwCuk6s8sxB4rdaCKI 2011-12-20 08:34:19 84.19.178.6 9001 0
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof
w Bandwidth=518000
p accept 43,53,79-81,110,143,194,220,443,953,989-990,993,995,1194,1293,1723,1863,2082-2083,2086-2087,2095-2096,3128,4321,5050,5190,5222-5223,6679,6697,7771,8000,8008,8080-8081,8090,8118,8123,8181,8300,8443,8888
.''')
        self.assertTrue('fake' in self.state.routers.keys())
        self.assertTrue('PPrivCom012' in self.state.routers.keys())

    def test_router_factory(self):
        self.state._update_network_status('''ns/all=
r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof
w Bandwidth=518000
p accept 43,53,79-81,110,143,194,220,443,953,989-990,993,995,1194,1293,1723,1863,2082-2083,2086-2087,2095-2096,3128,4321,5050,5190,5222-5223,6679,6697,7771,8000,8008,8080-8081,8090,8118,8123,8181,8300,8443,8888
r fake YxxmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof
w Bandwidth=543000
p accept 43,53
.''')
        self.assertTrue('$624926802351575FF7E4E3D60EFA3BFB56E67E8A' in self.state.routers)
        r = self.state.routers['$624926802351575FF7E4E3D60EFA3BFB56E67E8A']
        self.assertEqual(r.controller, self.state.protocol)
        self.assertEqual(r.bandwidth, 518000)
        self.assertEqual(len(self.state.routers_by_name['fake']), 2)

        # now we do an update
        self.state._update_network_status('''ns/all=
r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid FutureProof Authority
w Bandwidth=543000
p accept 43,53,79-81,110,143,194,220,443,953,989-990,993,995,1194,1293,1723,1863,2082-2083,2086-2087,2095-2096,3128,4321,5050,5190,5222-5223,6679,6697,7771,8000,8008,8080-8081,8090,8118,8123,8181,8300,8443,8888
.''')
        self.assertEqual(r.bandwidth, 543000)

    def test_empty_stream_update(self):
        self.state._stream_update('''stream-status=''')

    def test_addrmap(self):
        self.state._addr_map('example.com 127.0.0.1 "2012-01-01 00:00:00" EXPIRES=NEVER')

    def test_double_newconsensus(self):
        """
        The arrival of a second NEWCONSENSUS event causes parsing
        errors.
        """

        # bootstrap the TorState so we can send it a "real" 650
        # update

        self.protocol._set_valid_events(' '.join(self.state.event_map.keys()))
        self.state._bootstrap()

        self.send(b"250+ns/all=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250+circuit-status=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250-stream-status=")
        self.send(b"250 OK")

        self.send(b"250-address-mappings/all=")
        self.send(b'250 OK')

        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.send(b"250-entry-guards=")
        self.send(b"250 OK")

        self.send(b"250 OK")

        # state is now bootstrapped, we can send our NEWCONSENSUS update

        self.protocol.dataReceived(b'\r\n'.join(b'''650+NEWCONSENSUS
r Unnamed ABJlguUFz1lvQS0jq8nhTdRiXEk /zIVUg1tKMUeyUBoyimzorbQN9E 2012-05-23 01:10:22 219.94.255.254 9001 0
s Fast Guard Running Stable Valid
w Bandwidth=166
p reject 1-65535
.
650 OK
'''.split(b'\n')))

        self.protocol.dataReceived(b'\r\n'.join(b'''650+NEWCONSENSUS
r Unnamed ABJlguUFz1lvQS0jq8nhTdRiXEk /zIVUg1tKMUeyUBoyimzorbQN9E 2012-05-23 01:10:22 219.94.255.254 9001 0
s Fast Guard Running Stable Valid
w Bandwidth=166
p reject 1-65535
.
650 OK
'''.split(b'\n')))

        self.assertEqual(1, len(self.state.all_routers))
        self.assertTrue('Unnamed' in self.state.routers)
        self.assertTrue('$00126582E505CF596F412D23ABC9E14DD4625C49' in self.state.routers)

    def test_NEWCONSENSUS_ends_with_OK_on_w(self):
        """
        The arrival of a second NEWCONSENSUS event causes parsing
        errors.
        """

        # bootstrap the TorState so we can send it a "real" 650
        # update

        self.protocol._set_valid_events(' '.join(self.state.event_map.keys()))
        self.state._bootstrap()

        self.send(b"250+ns/all=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250+circuit-status=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250-stream-status=")
        self.send(b"250 OK")

        self.send(b"250-address-mappings/all=")
        self.send(b"250 OK")

        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.send(b"250-entry-guards=")
        self.send(b"250 OK")

        self.send(b"250 OK")

        # state is now bootstrapped, we can send our NEWCONSENSUS update

        self.protocol.dataReceived(b'\r\n'.join(b'''650+NEWCONSENSUS
r Unnamed ABJlguUFz1lvQS0jq8nhTdRiXEk /zIVUg1tKMUeyUBoyimzorbQN9E 2012-05-23 01:10:22 219.94.255.254 9001 0
s Fast Guard Running Stable Valid
w Bandwidth=166
.
650 OK
'''.split(b'\n')))

        self.assertTrue('Unnamed' in self.state.routers)
        self.assertTrue('$00126582E505CF596F412D23ABC9E14DD4625C49' in self.state.routers)

    def test_NEWCONSENSUS_ends_with_OK_on_s(self):
        """
        The arrival of a second NEWCONSENSUS event causes parsing
        errors.
        """

        # bootstrap the TorState so we can send it a "real" 650
        # update

        self.protocol._set_valid_events(' '.join(self.state.event_map.keys()))
        self.state._bootstrap()

        self.send(b"250+ns/all=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250+circuit-status=")
        self.send(b".")
        self.send(b"250 OK")

        self.send(b"250-stream-status=")
        self.send(b"250 OK")

        self.send(b"250-address-mappings/all=")
        self.send(b"250 OK")

        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        self.send(b"250-entry-guards=")
        self.send(b"250 OK")

        self.send(b"250 OK")

        # state is now bootstrapped, we can send our NEWCONSENSUS update

        self.protocol.dataReceived(b'\r\n'.join(b'''650+NEWCONSENSUS
r Unnamed ABJlguUFz1lvQS0jq8nhTdRiXEk /zIVUg1tKMUeyUBoyimzorbQN9E 2012-05-23 01:10:22 219.94.255.254 9001 0
s Fast Guard Running Stable Valid
.
650 OK
'''.split(b'\n')))

        self.assertTrue('Unnamed' in self.state.routers)
        self.assertTrue('$00126582E505CF596F412D23ABC9E14DD4625C49' in self.state.routers)

    def test_stream_create(self):
        self.state._stream_update('1610 NEW 0 1.2.3.4:56')
        self.assertTrue(1610 in self.state.streams)

    def test_stream_destroy(self):
        self.state._stream_update('1610 NEW 0 1.2.3.4:56')
        self.assertTrue(1610 in self.state.streams)
        self.state._stream_update("1610 FAILED 0 www.example.com:0 REASON=DONE REMOTE_REASON=FAILED")
        self.assertTrue(1610 not in self.state.streams)

    def test_stream_detach(self):
        circ = FakeCircuit(1)
        circ.state = 'BUILT'
        self.state.circuits[1] = circ

        self.state._stream_update('1610 NEW 0 1.2.3.4:56')
        self.assertTrue(1610 in self.state.streams)
        self.state._stream_update("1610 SUCCEEDED 1 4.3.2.1:80")
        self.assertEqual(self.state.streams[1610].circuit, circ)

        self.state._stream_update("1610 DETACHED 0 www.example.com:0 REASON=DONE REMOTE_REASON=FAILED")
        self.assertEqual(self.state.streams[1610].circuit, None)

    def test_stream_listener(self):
        self.protocol._set_valid_events('CIRC STREAM ORCONN BW DEBUG INFO NOTICE WARN ERR NEWDESC ADDRMAP AUTHDIR_NEWDESCS DESCCHANGED NS STATUS_GENERAL STATUS_CLIENT STATUS_SERVER GUARD STREAM_BW CLIENTS_SEEN NEWCONSENSUS BUILDTIMEOUT_SET')
        self.state._add_events()
        for ignored in self.state.event_map.items():
            self.send(b"250 OK")

        expected = [('new', {}),
                    ]
        listen = StreamListener(expected)
        self.send(b"650 STREAM 77 NEW 0 www.yahoo.cn:80 SOURCE_ADDR=127.0.0.1:54315 PURPOSE=USER")
        self.state.add_stream_listener(listen)

        self.assertEqual(1, len(self.state.streams.values()))
        self.assertTrue(listen in list(self.state.streams.values())[0].listeners)
        self.assertEqual(len(self.state.streams), 1)
        self.assertEqual(len(listen.expected), 1)

        self.send(b"650 STREAM 78 NEW 0 www.yahoo.cn:80 SOURCE_ADDR=127.0.0.1:54315 PURPOSE=USER")
        self.assertEqual(len(self.state.streams), 2)
        self.assertEqual(len(listen.expected), 0)

    def test_build_circuit(self):
        class FakeRouter:
            def __init__(self, i):
                self.id_hex = i
                self.flags = []

        path = []
        for x in range(3):
            path.append(FakeRouter("$%040d" % x))
        # can't just check flags for guard status, need to know if
        # it's in the running Tor's notion of Entry Guards
        path[0].flags = ['guard']

        self.state.build_circuit(path, using_guards=True)
        self.assertEqual(self.transport.value(), b'EXTENDCIRCUIT 0 0000000000000000000000000000000000000000,0000000000000000000000000000000000000001,0000000000000000000000000000000000000002\r\n')
        # should have gotten a warning about this not being an entry
        # guard
        self.assertEqual(len(self.flushWarnings()), 1)

    def test_build_circuit_no_routers(self):
        self.state.build_circuit()
        self.assertEqual(self.transport.value(), b'EXTENDCIRCUIT 0\r\n')

    def test_build_circuit_unfound_router(self):
        self.state.build_circuit(routers=[b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'], using_guards=False)
        self.assertEqual(self.transport.value(), b'EXTENDCIRCUIT 0 AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\r\n')

    def circuit_callback(self, circ):
        self.assertTrue(isinstance(circ, Circuit))
        self.assertEqual(circ.id, 1234)

    def test_build_circuit_final_callback(self):
        class FakeRouter:
            def __init__(self, i):
                self.id_hex = i
                self.flags = []

        path = []
        for x in range(3):
            path.append(FakeRouter("$%040d" % x))
        # can't just check flags for guard status, need to know if
        # it's in the running Tor's notion of Entry Guards
        path[0].flags = ['guard']

        # FIXME TODO we should verify we get a circuit_new event for
        # this circuit

        d = self.state.build_circuit(path, using_guards=True)
        d.addCallback(self.circuit_callback)
        self.assertEqual(self.transport.value(), b'EXTENDCIRCUIT 0 0000000000000000000000000000000000000000,0000000000000000000000000000000000000001,0000000000000000000000000000000000000002\r\n')
        self.send(b"250 EXTENDED 1234")
        # should have gotten a warning about this not being an entry
        # guard
        self.assertEqual(len(self.flushWarnings()), 1)
        return d

    def test_build_circuit_error(self):
        """
        tests that we check the callback properly
        """

        try:
            self.state._find_circuit_after_extend("FOO 1234")
            self.assertTrue(False)
        except RuntimeError as e:
            self.assertTrue('Expected EXTENDED' in str(e))

    def test_listener_mixins(self):
        self.assertTrue(verifyClass(IStreamListener, StreamListenerMixin))
        self.assertTrue(verifyClass(ICircuitListener, CircuitListenerMixin))

    def test_build_circuit_timedout(self):
        class FakeRouter:
            def __init__(self, i):
                self.id_hex = i
                self.flags = []

        path = []
        for x in range(3):
            path.append(FakeRouter("$%040d" % x))
        # can't just check flags for guard status, need to know if
        # it's in the running Tor's notion of Entry Guards
        path[0].flags = ['guard']

        # FIXME TODO we should verify we get a circuit_new event for
        # this circuit
        timeout = 10
        clock = task.Clock()

        d = build_timeout_circuit(self.state, clock, path, timeout, using_guards=False)
        clock.advance(10)

        def check_for_timeout_error(f):
            self.assertTrue(isinstance(f.type(), CircuitBuildTimedOutError))
        d.addErrback(check_for_timeout_error)
        return d

    def test_build_circuit_timeout_after_progress(self):
        """
        Similar to above but we timeout after Tor has ack'd our
        circuit-creation attempt, but before reaching BUILT.
        """
        class FakeRouter:
            def __init__(self, i):
                self.id_hex = i
                self.flags = []

        class FakeCircuit(Circuit):
            def close(self):
                return defer.succeed(None)

        path = []
        for x in range(3):
            path.append(FakeRouter("$%040d" % x))

        def fake_queue(cmd):
            self.assertTrue(cmd.startswith('EXTENDCIRCUIT 0'))
            return defer.succeed("EXTENDED 1234")

        queue_command = patch.object(self.protocol, 'queue_command', fake_queue)
        circuit_factory = patch.object(self.state, 'circuit_factory', FakeCircuit)
        with queue_command, circuit_factory:
            timeout = 10
            clock = task.Clock()

            d = build_timeout_circuit(self.state, clock, path, timeout, using_guards=False)
            clock.advance(timeout + 1)

            def check_for_timeout_error(f):
                self.assertTrue(isinstance(f.type(), CircuitBuildTimedOutError))
            d.addErrback(check_for_timeout_error)
        return d

    def test_build_circuit_not_timedout(self):
        class FakeRouter:
            def __init__(self, i):
                self.id_hex = i
                self.flags = []

        path = []
        for x in range(3):
            path.append(FakeRouter("$%040d" % x))
        path[0].flags = ['guard']

        timeout = 10
        clock = task.Clock()
        d = build_timeout_circuit(self.state, clock, path, timeout, using_guards=True)
        d.addCallback(self.circuit_callback)

        self.assertEqual(self.transport.value(), b'EXTENDCIRCUIT 0 0000000000000000000000000000000000000000,0000000000000000000000000000000000000001,0000000000000000000000000000000000000002\r\n')
        self.send(b"250 EXTENDED 1234")
        # we can't just .send(b'650 CIRC 1234 BUILT') this because we
        # didn't fully hook up the protocol to the state, e.g. via
        # post_bootstrap etc.
        self.state.circuits[1234].update(['1234', 'BUILT'])
        # should have gotten a warning about this not being an entry
        # guard
        self.assertEqual(len(self.flushWarnings()), 1)
        return d
