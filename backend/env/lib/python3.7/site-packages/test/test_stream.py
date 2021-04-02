from __future__ import print_function

from txtorcon.util import maybe_ip_addr
from twisted.trial import unittest
from twisted.internet import defer
from zope.interface import implementer

from txtorcon import Stream
from txtorcon import IStreamListener
from txtorcon import ICircuitContainer
from txtorcon import StreamListenerMixin
from txtorcon import AddrMap


class FakeCircuit:
    def __init__(self, id=-999):
        self.streams = []
        self.id = id


@implementer(IStreamListener)
class Listener(object):

    def __init__(self, expected):
        "expect is a list of tuples: (event, {key:value, key1:value1, ..})"
        self.expected = expected

    def checker(self, state, stream, *args, **kw):
        if self.expected[0][0] != state:
            raise RuntimeError(
                'Expected event "%s" not "%s".' % (self.expected[0][0], state)
            )
        for (k, v) in self.expected[0][1].items():
            if k == 'args':
                if v != args:
                    raise RuntimeError(
                        'Expected argument to have value "%s", not "%s"' % (v, args)
                    )
            elif k == 'kwargs':
                for (key, value) in v.items():
                    if key not in kw:
                        print(key, value, k, v, kw)
                        raise RuntimeError(
                            'Expected keyword argument for key "%s" but found nothing.' % key
                        )
                    elif kw[key] != value:
                        raise RuntimeError(
                            'KW Argument expected "%s" but got "%s"' %
                            (value, kw[key])
                        )
            elif getattr(stream, k) != v:
                raise RuntimeError(
                    'Expected attribute "%s" to have value "%s", not "%s"' %
                    (k, v, getattr(stream, k))
                )
        self.expected = self.expected[1:]

    def stream_new(self, stream):
        "a new stream has been created"
        self.checker('new', stream)

    def stream_succeeded(self, stream):
        "stream has succeeded"
        self.checker('succeeded', stream)

    def stream_attach(self, stream, circuit):
        "the stream has been attached to a circuit"
        self.checker('attach', stream, circuit)

    def stream_detach(self, stream, **kw):
        "the stream has been attached to a circuit"
        self.checker('detach', stream, **kw)

    def stream_closed(self, stream, **kw):
        "stream has been closed (won't be in controller's list anymore)"
        self.checker('closed', stream, **kw)

    def stream_failed(self, stream, **kw):
        "stream failed for some reason (won't be in controller's list anymore)"
        self.checker('failed', stream, **kw)


@implementer(ICircuitContainer)
class StreamTests(unittest.TestCase):

    def find_circuit(self, id):
        return self.circuits[id]

    def close_circuit(self, circuit, **kw):
        raise NotImplementedError()

    def close_stream(self, stream, **kw):
        return defer.succeed('')

    def setUp(self):
        self.circuits = {}

    def test_lowercase_flags(self):
        # testing an internal method, maybe a no-no?
        stream = Stream(self)
        kw = dict(FOO='bar', BAR='baz')
        flags = stream._create_flags(kw)
        self.assertTrue('FOO' in flags)
        self.assertTrue('foo' in flags)
        self.assertTrue(flags['foo'] is flags['FOO'])

        self.assertTrue('BAR' in flags)
        self.assertTrue('bar' in flags)
        self.assertTrue(flags['bar'] is flags['BAR'])

    def test_listener_mixin(self):
        listener = StreamListenerMixin()
        from zope.interface.verify import verifyObject
        self.assertTrue(verifyObject(IStreamListener, listener))

        # call all the methods with None for each arg. This is mostly
        # just to gratuitously increase test coverage, but also
        # serves to ensure these methods don't just blow up
        for (methodname, desc) in IStreamListener.namesAndDescriptions():
            method = getattr(listener, methodname)
            args = [None] * len(desc.positional)
            method(*args)

    def test_listener_exception(self):
        """A listener throws an exception during notify"""

        exc = Exception("the bad stuff happened")

        class Bad(StreamListenerMixin):
            def stream_new(*args, **kw):
                raise exc
        listener = Bad()

        stream = Stream(self)
        stream.listen(listener)
        stream.update("1 NEW 0 94.23.164.42.$43ED8310EB968746970896E8835C2F1991E50B69.exit:9001 SOURCE_ADDR=(Tor_internal):0 PURPOSE=DIR_FETCH".split())

        errors = self.flushLoggedErrors()
        self.assertEqual(1, len(errors))
        self.assertEqual(errors[0].value, exc)

    def test_stream_addrmap_remap(self):
        addrmap = AddrMap()
        addrmap.update('meejah.ca 1.2.3.4 never')
        stream = Stream(self, addrmap)
        stream.update("1604 NEW 0 1.2.3.4:0 PURPOSE=DNS_REQUEST".split())
        self.assertEqual(stream.target_host, "meejah.ca")

    def test_circuit_already_valid_in_new(self):
        stream = Stream(self)
        stream.circuit = FakeCircuit(1)
        stream.update("1 NEW 0 94.23.164.42.$43ED8310EB968746970896E8835C2F1991E50B69.exit:9001 SOURCE_ADDR=(Tor_internal):0 PURPOSE=DIR_FETCH".split())
        errs = self.flushLoggedErrors()
        self.assertEqual(len(errs), 1)
        self.assertTrue('Weird' in errs[0].getErrorMessage())

    def test_magic_circuit_detach(self):
        stream = Stream(self)
        stream.circuit = FakeCircuit(1)
        stream.circuit.streams = [stream]
        stream.update("1 SENTCONNECT 0 94.23.164.42.$43ED8310EB968746970896E8835C2F1991E50B69.exit:9001 SOURCE_ADDR=(Tor_internal):0 PURPOSE=DIR_FETCH".split())
        self.assertTrue(stream.circuit is None)

    def test_args_in_ctor(self):
        stream = Stream(self)
        stream.update("1 NEW 0 94.23.164.42.$43ED8310EB968746970896E8835C2F1991E50B69.exit:9001 SOURCE_ADDR=(Tor_internal):0 PURPOSE=DIR_FETCH".split())
        self.assertEqual(stream.id, 1)
        self.assertEqual(stream.state, 'NEW')

    def test_parse_resolve(self):
        stream = Stream(self)
        stream.update("1604 NEWRESOLVE 0 www.google.ca:0 PURPOSE=DNS_REQUEST".split())
        self.assertEqual(stream.state, 'NEWRESOLVE')

    def test_listener_new(self):
        listener = Listener([('new', {'target_port': 9001})])

        stream = Stream(self)
        stream.listen(listener)
        stream.update("1 NEW 0 94.23.164.42.$43ED8310EB968746970896E8835C2F1991E50B69.exit:9001 SOURCE_ADDR=(Tor_internal):0 PURPOSE=DIR_FETCH".split())

    def test_listener_attach(self):
        self.circuits[186] = FakeCircuit(186)

        listener = Listener(
            [
                ('new', {'target_host': 'www.yahoo.com', 'target_port': 80}),
                ('attach', {'target_addr': maybe_ip_addr('1.2.3.4')})
            ]
        )

        stream = Stream(self)
        stream.listen(listener)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        stream.update("316 REMAP 186 1.2.3.4:80 SOURCE=EXIT".split())

        self.assertEqual(self.circuits[186].streams[0], stream)

    def test_listener_attach_no_remap(self):
        "Attachment is via SENTCONNECT on .onion addresses (for example)"
        self.circuits[186] = FakeCircuit(186)

        listener = Listener([('new', {'target_host': 'www.yahoo.com',
                                      'target_port': 80}),
                             ('attach', {})])

        stream = Stream(self)
        stream.listen(listener)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        stream.update("316 SENTCONNECT 186 1.2.3.4:80 SOURCE=EXIT".split())

        self.assertEqual(self.circuits[186].streams[0], stream)

    def test_update_wrong_stream(self):
        self.circuits[186] = FakeCircuit(186)

        stream = Stream(self)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        try:
            stream.update("999 SENTCONNECT 186 1.2.3.4:80 SOURCE=EXIT".split())
            self.fail()
        except Exception as e:
            self.assertTrue('wrong stream' in str(e))

    def test_update_illegal_state(self):
        self.circuits[186] = FakeCircuit(186)

        stream = Stream(self)
        try:
            stream.update("316 FOO 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
            self.fail()
        except Exception as e:
            self.assertTrue('Unknown state' in str(e))

    def test_listen_unlisten(self):
        self.circuits[186] = FakeCircuit(186)

        listener = Listener([])

        stream = Stream(self)
        stream.listen(listener)
        stream.listen(listener)
        self.assertEqual(len(stream.listeners), 1)
        stream.unlisten(listener)
        self.assertEqual(len(stream.listeners), 0)

    def test_stream_changed(self):
        "Change a stream-id mid-stream."
        self.circuits[186] = FakeCircuit(186)

        listener = Listener([('new', {'target_host': 'www.yahoo.com',
                                      'target_port': 80}),
                             ('attach', {}),
                             ('succeeded', {})])

        stream = Stream(self)
        stream.listen(listener)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        stream.update("316 SENTCONNECT 186 1.2.3.4:80 SOURCE=EXIT".split())
        self.assertEqual(self.circuits[186].streams[0], stream)

        # magically change circuit ID without a DETACHED, should fail
        stream.update("316 SUCCEEDED 999 1.2.3.4:80 SOURCE=EXIT".split())
        errs = self.flushLoggedErrors()
        self.assertEqual(len(errs), 1)
        # kind of fragile to look at strings, but...
        self.assertTrue('186 to 999' in str(errs[0]))

    def test_stream_changed_with_detach(self):
        "Change a stream-id mid-stream, but with a DETACHED message"
        self.circuits[123] = FakeCircuit(123)
        self.circuits[456] = FakeCircuit(456)

        listener = Listener(
            [
                ('new', {'target_host': 'www.yahoo.com', 'target_port': 80}),
                ('attach', {}),
                ('detach', {'kwargs': dict(reason='END', remote_reason='MISC')}),
                ('attach', {})
            ]
        )

        stream = Stream(self)
        stream.listen(listener)
        stream.update("999 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        stream.update("999 SENTCONNECT 123 1.2.3.4:80".split())
        self.assertEqual(len(self.circuits[123].streams), 1)
        self.assertEqual(self.circuits[123].streams[0], stream)

        stream.update("999 DETACHED 123 1.2.3.4:80 REASON=END REMOTE_REASON=MISC".split())
        self.assertEqual(len(self.circuits[123].streams), 0)

        stream.update("999 SENTCONNECT 456 1.2.3.4:80 SOURCE=EXIT".split())
        self.assertEqual(len(self.circuits[456].streams), 1)
        self.assertEqual(self.circuits[456].streams[0], stream)

    def test_listener_close(self):
        self.circuits[186] = FakeCircuit(186)

        listener = Listener(
            [
                ('new', {'target_host': 'www.yahoo.com', 'target_port': 80}),
                ('attach', {'target_addr': maybe_ip_addr('1.2.3.4')}),
                ('closed', {'kwargs': dict(REASON='END', REMOTE_REASON='DONE')})
            ]
        )
        stream = Stream(self)
        stream.listen(listener)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        stream.update("316 REMAP 186 1.2.3.4:80 SOURCE=EXIT".split())
        stream.update("316 CLOSED 186 1.2.3.4:80 REASON=END REMOTE_REASON=DONE".split())

        self.assertEqual(len(self.circuits[186].streams), 0)

    def test_listener_fail(self):
        listener = Listener(
            [
                ('new', {'target_host': 'www.yahoo.com', 'target_port': 80}),
                ('attach', {'target_addr': maybe_ip_addr('1.2.3.4')}),
                ('failed', {'kwargs': dict(REASON='TIMEOUT', REMOTE_REASON='DESTROYED')})
            ]
        )
        stream = Stream(self)
        stream.listen(listener)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        self.circuits[186] = FakeCircuit(186)
        stream.update("316 REMAP 186 1.2.3.4:80 SOURCE=EXIT".split())
        stream.update("316 FAILED 0 1.2.3.4:80 REASON=TIMEOUT REMOTE_REASON=DESTROYED".split())

    def test_str(self):
        stream = Stream(self)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        stream.circuit = FakeCircuit(1)
        str(stream)

    def test_ipv6(self):
        listener = Listener([('new', {'target_host': '::1',
                                      'target_port': 80})])

        stream = Stream(self)
        stream.listen(listener)
        stream.update("1234 NEW 0 ::1:80 SOURCE_ADDR=127.0.0.1:57349 PURPOSE=USER".split())

    def test_ipv6_remap(self):
        stream = Stream(self)
        stream.update("1234 REMAP 0 ::1:80 SOURCE_ADDR=127.0.0.1:57349 PURPOSE=USER".split())
        self.assertEqual(stream.target_addr, maybe_ip_addr('::1'))

    def test_ipv6_source(self):
        listener = Listener(
            [
                ('new', {'source_addr': maybe_ip_addr('::1'),
                         'source_port': 12345})
            ]
        )

        stream = Stream(self)
        stream.listen(listener)
        stream.update("1234 NEW 0 127.0.0.1:80 SOURCE_ADDR=::1:12345 PURPOSE=USER".split())

    def test_states_and_uris(self):
        self.circuits[1] = FakeCircuit(1)

        stream = Stream(self)
        for address in [
                '1.2.3.4:80',
                '1.2.3.4.315D5684D5343580D409F16119F78D776A58AEFB.exit:80',
                'timaq4ygg2iegci7.onion:80']:

            line = "316 %s 1 %s REASON=FOO"
            for state in ['NEW', 'SUCCEEDED', 'REMAP',
                          'SENTCONNECT',
                          'DETACHED', 'NEWRESOLVE', 'SENTRESOLVE',
                          'FAILED', 'CLOSED']:
                stream.update((line % (state, address)).split(' '))
                self.assertEqual(stream.state, state)

    def test_close_stream(self):
        self.circuits[186] = FakeCircuit(186)
        stream = Stream(self)
        stream.update("316 NEW 0 www.yahoo.com:80 SOURCE_ADDR=127.0.0.1:55877 PURPOSE=USER".split())
        stream.update("316 REMAP 186 1.2.3.4:80 SOURCE=EXIT".split())

        self.assertEqual(len(self.circuits[186].streams), 1)

        d = stream.close()
        self.assertTrue(not d.called)
        self.assertEqual(len(self.circuits[186].streams), 1)

        stream.update("316 CLOSED 186 1.2.3.4:80 REASON=END REMOTE_REASON=DONE".split())
        self.assertTrue(d.called)
        self.assertEqual(len(self.circuits[186].streams), 0)
