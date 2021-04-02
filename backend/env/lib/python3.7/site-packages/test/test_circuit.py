import datetime
import ipaddress
from mock import patch

from twisted.trial import unittest
from twisted.internet import defer
from twisted.python.failure import Failure

from zope.interface import implementer

from txtorcon import Circuit
from txtorcon import Stream
from txtorcon import TorControlProtocol
from txtorcon import TorState
from txtorcon import Router
from txtorcon.router import hexIdFromHash
from txtorcon.circuit import TorCircuitEndpoint, _get_circuit_attacher
from txtorcon.interface import IRouterContainer
from txtorcon.interface import ICircuitListener
from txtorcon.interface import ICircuitContainer
from txtorcon.interface import CircuitListenerMixin
from txtorcon.interface import ITorControlProtocol

from mock import Mock


@implementer(IRouterContainer)
@implementer(ICircuitListener)
@implementer(ICircuitContainer)
@implementer(ITorControlProtocol)
class FakeTorController(object):

    post_bootstrap = defer.Deferred()
    queue_command = Mock()

    def __init__(self):
        self.routers = {}
        self.circuits = {}
        self.extend = []
        self.failed = []

    def router_from_id(self, i):
        return self.routers[i[:41]]

    def circuit_new(self, circuit):
        self.circuits[circuit.id] = circuit

    def circuit_extend(self, circuit, router):
        self.extend.append((circuit, router))

    def circuit_launched(self, circuit):
        pass

    def circuit_built(self, circuit):
        pass

    def circuit_closed(self, circuit, **kw):
        if circuit.id in self.circuits:
            del self.circuits[circuit.id]

    def circuit_failed(self, circuit, **kw):
        self.failed.append((circuit, kw))
        if circuit.id in self.circuits:
            del self.circuits[circuit.id]

    def find_circuit(self, circid):
        return self.circuits[circid]

    def close_circuit(self, circid):
        del self.circuits[circid]
        return defer.succeed('')


class FakeLocation:

    def __init__(self):
        self.countrycode = 'NA'


class FakeRouter:

    def __init__(self, hsh, nm):
        self.name = nm
        self.id_hash = hsh
        self.id_hex = hexIdFromHash(self.id_hash)
        self.location = FakeLocation()


examples = ['CIRC 365 LAUNCHED PURPOSE=GENERAL',
            'CIRC 365 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris PURPOSE=GENERAL',
            'CIRC 365 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus PURPOSE=GENERAL',
            'CIRC 365 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL',
            'CIRC 365 BUILT $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL',
            'CIRC 365 CLOSED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=FINISHED',
            'CIRC 365 FAILED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=TIMEOUT']


class TestCircuitEndpoint(unittest.TestCase):

    @defer.inlineCallbacks
    def test_attach(self):

        @implementer(ICircuitContainer)
        class FakeContainer(object):
            pass

        container = FakeContainer()
        stream = Stream(container)
        circuit = Mock()
        target_endpoint = Mock()
        reactor = Mock()
        state = Mock()

        TorCircuitEndpoint(
            reactor, state, circuit, target_endpoint,
        )

        attacher = yield _get_circuit_attacher(reactor, state)
        attacher.add_endpoint(target_endpoint, circuit)
        yield attacher.attach_stream(stream, [])
        # hmmm, no assert??

    @defer.inlineCallbacks
    def test_attach_stream_failure(self):

        @implementer(ICircuitContainer)
        class FakeContainer(object):
            pass

        container = FakeContainer()
        stream = Stream(container)
        stream.source_addr = ipaddress.IPv4Address(u'0.0.0.0')
        stream.source_port = 12345
        circuit = Mock()
        circuit.when_built = Mock(return_value=Failure(Exception('testing1234')))
        target_endpoint = Mock()
        src_addr = Mock()
        src_addr.host = u'0.0.0.0'
        src_addr.port = 12345
        target_endpoint._get_address = Mock(return_value=defer.succeed(src_addr))
        reactor = Mock()
        state = Mock()

        TorCircuitEndpoint(
            reactor, state, circuit, target_endpoint,
        )

        attacher = yield _get_circuit_attacher(reactor, state)
        d = attacher.add_endpoint(target_endpoint, circuit)
        self.assertEqual(len(attacher._circuit_targets), 1)
        # this will fail, but should be ignored
        yield attacher.attach_stream(stream, [])
        with self.assertRaises(Exception) as ctx:
            yield d
        self.assertTrue("testing1234" in str(ctx.exception))

    @defer.inlineCallbacks
    def test_attach_failure_unfound(self):

        @implementer(ICircuitContainer)
        class FakeContainer(object):
            pass

        reactor = Mock()
        container = FakeContainer()
        stream = Stream(container)
        state = Mock()

        attacher = yield _get_circuit_attacher(reactor, state)
        attacher.attach_stream_failure(stream, None)
        # no assert; just making sure this doesn't explode


class CircuitTests(unittest.TestCase):

    def test_age(self):
        """
        make sure age does something sensible at least once.
        """
        tor = FakeTorController()

        circuit = Circuit(tor)
        now = datetime.datetime.now()
        update = '1 LAUNCHED PURPOSE=GENERAL TIME_CREATED=%s' % now.strftime('%Y-%m-%dT%H:%M:%S')
        circuit.update(update.split())
        diff = circuit.age(now=now)
        self.assertEqual(diff, 0)
        self.assertTrue(circuit.time_created is not None)

    @patch('txtorcon.circuit.datetime')
    def test_age_default(self, fake_datetime):
        """
        age() w/ defaults works properly
        """
        from datetime import datetime
        now = datetime.fromtimestamp(60.0)
        fake_datetime.return_value = now
        fake_datetime.utcnow = Mock(return_value=now)
        tor = FakeTorController()

        circuit = Circuit(tor)
        circuit._time_created = datetime.fromtimestamp(0.0)
        self.assertEqual(circuit.age(), 60)
        self.assertTrue(circuit.time_created is not None)

    def test_no_age_yet(self):
        """
        make sure age doesn't explode if there's no TIME_CREATED flag.
        """
        tor = FakeTorController()

        circuit = Circuit(tor)
        now = datetime.datetime.now()
        circuit.update('1 LAUNCHED PURPOSE=GENERAL'.split())
        self.assertTrue(circuit.time_created is None)
        diff = circuit.age(now=now)
        self.assertEqual(diff, None)

    def test_listener_mixin(self):
        listener = CircuitListenerMixin()
        from zope.interface.verify import verifyObject
        self.assertTrue(verifyObject(ICircuitListener, listener))

        # call all the methods with None for each arg. This is mostly
        # just to gratuitously increase test coverage, but also
        # serves to ensure these methods don't just blow up
        for (methodname, desc) in ICircuitListener.namesAndDescriptions():
            method = getattr(listener, methodname)
            args = [None] * len(desc.positional)
            method(*args)

    def test_unlisten(self):
        tor = FakeTorController()
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = FakeRouter(
            '$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a'
        )

        circuit = Circuit(tor)
        circuit.listen(tor)
        circuit.listen(tor)
        circuit.update('1 LAUNCHED PURPOSE=GENERAL'.split())
        circuit.unlisten(tor)
        circuit.update('1 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris PURPOSE=GENERAL'.split())
        self.assertEqual(len(tor.circuits), 1)
        self.assertTrue(1 in tor.circuits)
        self.assertEqual(len(tor.extend), 0)
        self.assertEqual(1, len(circuit.path))
        self.assertEqual(0, len(circuit.listeners))

    def test_path_update(self):
        cp = TorControlProtocol()
        state = TorState(cp, False)
        circuit = Circuit(state)
        circuit.update('1 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris PURPOSE=GENERAL'.split())
        self.assertEqual(1, len(circuit.path))
        self.assertEqual(
            '$E11D2B2269CC25E67CA6C9FB5843497539A74FD0',
            circuit.path[0].id_hex
        )
        self.assertEqual('eris', circuit.path[0].name)

    def test_wrong_update(self):
        tor = FakeTorController()
        circuit = Circuit(tor)
        circuit.listen(tor)
        circuit.update('1 LAUNCHED PURPOSE=GENERAL'.split())
        self.assertRaises(
            Exception,
            circuit.update,
            '2 LAUNCHED PURPOSE=GENERAL'.split()
        )

    def test_closed_remaining_streams(self):
        tor = FakeTorController()
        circuit = Circuit(tor)
        circuit.listen(tor)
        circuit.update('1 LAUNCHED PURPOSE=GENERAL'.split())
        stream = Stream(tor)
        stream.update("1 NEW 0 94.23.164.42.$43ED8310EB968746970896E8835C2F1991E50B69.exit:9001 SOURCE_ADDR=(Tor_internal):0 PURPOSE=DIR_FETCH".split())
        circuit.streams.append(stream)
        self.assertEqual(len(circuit.streams), 1)

        circuit.update('1 CLOSED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=FINISHED'.split())
        circuit.update('1 FAILED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=TIMEOUT'.split())
        errs = self.flushLoggedErrors()
        self.assertEqual(len(errs), 1)
        self.assertTrue('Circuit is FAILED but still has 1 streams' in str(errs[0]))

    def test_updates(self):
        tor = FakeTorController()
        circuit = Circuit(tor)
        circuit.listen(tor)
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = FakeRouter(
            '$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a'
        )
        tor.routers['$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5'] = FakeRouter(
            '$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5', 'b'
        )
        tor.routers['$253DFF1838A2B7782BE7735F74E50090D46CA1BC'] = FakeRouter(
            '$253DFF1838A2B7782BE7735F74E50090D46CA1BC', 'c'
        )

        for ex in examples[:-1]:
            circuit.update(ex.split()[1:])
            self.assertEqual(circuit.state, ex.split()[2])
            self.assertEqual(circuit.purpose, 'GENERAL')
            if '$' in ex:
                self.assertEqual(
                    len(circuit.path),
                    len(ex.split()[3].split(','))
                )
                for (r, p) in zip(ex.split()[3].split(','), circuit.path):
                    d = r.split('=')[0]
                    self.assertEqual(d, p.id_hash)

    def test_extend_messages(self):
        tor = FakeTorController()
        a = FakeRouter('$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a')
        b = FakeRouter('$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5', 'b')
        c = FakeRouter('$253DFF1838A2B7782BE7735F74E50090D46CA1BC', 'c')
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = a
        tor.routers['$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5'] = b
        tor.routers['$253DFF1838A2B7782BE7735F74E50090D46CA1BC'] = c

        circuit = Circuit(tor)
        circuit.listen(tor)

        circuit.update('365 LAUNCHED PURPOSE=GENERAL'.split())
        self.assertEqual(tor.extend, [])
        circuit.update('365 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris PURPOSE=GENERAL'.split())
        self.assertEqual(len(tor.extend), 1)
        self.assertEqual(tor.extend[0], (circuit, a))

        circuit.update('365 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus PURPOSE=GENERAL'.split())
        self.assertEqual(len(tor.extend), 2)
        self.assertEqual(tor.extend[0], (circuit, a))
        self.assertEqual(tor.extend[1], (circuit, b))

        circuit.update('365 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL'.split())
        self.assertEqual(len(tor.extend), 3)
        self.assertEqual(tor.extend[0], (circuit, a))
        self.assertEqual(tor.extend[1], (circuit, b))
        self.assertEqual(tor.extend[2], (circuit, c))

    def test_extends_no_path(self):
        '''
        without connectivity, it seems you get EXTENDS messages with no
        path update.
        '''
        tor = FakeTorController()
        circuit = Circuit(tor)
        circuit.listen(tor)

        circuit.update('753 EXTENDED BUILD_FLAGS=IS_INTERNAL,NEED_CAPACITY,NEED_UPTIME PURPOSE=MEASURE_TIMEOUT TIME_CREATED=2012-07-30T18:23:18.956704'.split())
        self.assertEqual(tor.extend, [])
        self.assertEqual(circuit.path, [])
        self.assertTrue('IS_INTERNAL' in circuit.build_flags)
        self.assertTrue('NEED_CAPACITY' in circuit.build_flags)
        self.assertTrue('NEED_UPTIME' in circuit.build_flags)

    def test_str(self):
        tor = FakeTorController()
        circuit = Circuit(tor)
        circuit.id = 1
        str(circuit)
        router = Router(tor)
        circuit.path.append(router)
        str(circuit)

    def test_failed_reason(self):
        tor = FakeTorController()
        circuit = Circuit(tor)
        circuit.listen(tor)
        circuit.update('1 FAILED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris PURPOSE=GENERAL REASON=TIMEOUT'.split())
        self.assertEqual(len(tor.failed), 1)
        circ, kw = tor.failed[0]
        self.assertEqual(circ, circuit)
        self.assertTrue('PURPOSE' in kw)
        self.assertTrue('REASON' in kw)
        self.assertEqual(kw['PURPOSE'], 'GENERAL')
        self.assertEqual(kw['REASON'], 'TIMEOUT')

    def test_close_circuit(self):
        tor = FakeTorController()
        a = FakeRouter('$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a')
        b = FakeRouter('$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5', 'b')
        c = FakeRouter('$253DFF1838A2B7782BE7735F74E50090D46CA1BC', 'c')
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = a
        tor.routers['$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5'] = b
        tor.routers['$253DFF1838A2B7782BE7735F74E50090D46CA1BC'] = c

        circuit = Circuit(tor)
        circuit.listen(tor)

        circuit.update('123 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL'.split())

        self.assertEqual(3, len(circuit.path))
        d0 = circuit.close()
        # we already pretended that Tor answered "OK" to the
        # CLOSECIRCUIT call (see close_circuit() in FakeTorController
        # above) however the circuit isn't "really" closed yet...
        self.assertTrue(not d0.result.called)
        # not unit-test-y? shouldn't probably delve into internals I
        # suppose...
        self.assertTrue(circuit._closing_deferred is not None)

        # if we try to close it again (*before* the actual close has
        # succeeded!) we should also still be waiting.
        d1 = circuit.close()
        self.assertTrue(not d1.called)
        # ...and this Deferred should *not* be the same as the first
        self.assertTrue(d0 is not d1)

        # simulate that Tor has really closed the circuit for us
        # this should cause our Deferred to callback
        circuit.update('123 CLOSED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL REASON=FINISHED'.split())

        # if we close *after* the close has succeeded, then we should
        # immediately "succeed"
        d2 = circuit.close()
        self.assertTrue(d1.called)

        # confirm that our circuit callback has been triggered already
        self.assertRaises(
            defer.AlreadyCalledError,
            d0.callback,
            "should have been called already"
        )
        return defer.DeferredList([d0, d1, d2])

    def test_is_built(self):
        tor = FakeTorController()
        a = FakeRouter('$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a')
        b = FakeRouter('$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5', 'b')
        c = FakeRouter('$253DFF1838A2B7782BE7735F74E50090D46CA1BC', 'c')
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = a
        tor.routers['$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5'] = b
        tor.routers['$253DFF1838A2B7782BE7735F74E50090D46CA1BC'] = c

        circuit = Circuit(tor)
        circuit.listen(tor)

        circuit.update('123 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL'.split())
        built0 = circuit.is_built
        built1 = circuit.when_built()

        self.assertTrue(built0 is not built1)
        self.assertFalse(built0.called)
        self.assertFalse(built1.called)

        circuit.update('123 BUILT $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL'.split())

        # create callback when we're alread in BUILT; should be
        # callback'd already
        built2 = circuit.when_built()

        self.assertTrue(built2 is not built1)
        self.assertTrue(built2 is not built0)
        self.assertTrue(built0.called)
        self.assertTrue(built1.called)
        self.assertTrue(built2.called)
        self.assertTrue(built0.result == circuit)
        self.assertTrue(built1.result == circuit)
        self.assertTrue(built2.result == circuit)

    def test_when_closed(self):
        tor = FakeTorController()
        a = FakeRouter('$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a')
        b = FakeRouter('$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5', 'b')
        c = FakeRouter('$253DFF1838A2B7782BE7735F74E50090D46CA1BC', 'c')
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = a
        tor.routers['$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5'] = b
        tor.routers['$253DFF1838A2B7782BE7735F74E50090D46CA1BC'] = c

        circuit = Circuit(tor)
        circuit.listen(tor)

        circuit.update('123 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL'.split())
        d0 = circuit.when_closed()

        self.assertFalse(d0.called)

        circuit.update('123 BUILT $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris,$50DD343021E509EB3A5A7FD0D8A4F8364AFBDCB5=venus,$253DFF1838A2B7782BE7735F74E50090D46CA1BC=chomsky PURPOSE=GENERAL'.split())
        circuit.update('123 CLOSED'.split())

        d1 = circuit.when_closed()

        self.assertTrue(d0 is not d1)
        self.assertTrue(d0.called)
        self.assertTrue(d1.called)

    def test_is_built_errback(self):
        tor = FakeTorController()
        a = FakeRouter('$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a')
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = a

        state = TorState(tor)
        circuit = Circuit(tor)
        circuit.listen(tor)

        circuit.update('123 EXTENDED $E11D2B2269CC25E67CA6C9FB5843497539A74FD0=eris PURPOSE=GENERAL'.split())
        state.circuit_new(circuit)
        d = circuit.when_built()

        called = []

        def err(f):
            called.append(f)
            return None
        d.addErrback(err)

        state.circuit_closed(circuit, REASON='testing')

        self.assertEqual(1, len(called))
        self.assertTrue(isinstance(called[0], Failure))
        self.assertTrue('testing' in str(called[0].value))
        return d

    def test_stream_success(self):
        tor = FakeTorController()
        a = FakeRouter('$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a')
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = a

        circuit = Circuit(tor)
        reactor = Mock()

        circuit.stream_via(
            reactor, 'torproject.org', 443,
            Mock(),
            use_tls=True,
        )

    def test_circuit_web_agent(self):
        tor = FakeTorController()
        a = FakeRouter('$E11D2B2269CC25E67CA6C9FB5843497539A74FD0', 'a')
        tor.routers['$E11D2B2269CC25E67CA6C9FB5843497539A74FD0'] = a

        circuit = Circuit(tor)
        reactor = Mock()

        # just testing this doesn't cause an exception
        circuit.web_agent(reactor, Mock())
