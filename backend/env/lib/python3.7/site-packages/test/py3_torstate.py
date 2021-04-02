from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet import defer
from twisted.internet.interfaces import IReactorCore

from zope.interface import implementer

from txtorcon import TorControlProtocol
from txtorcon import TorState
from txtorcon import Circuit
from txtorcon.interface import IStreamAttacher


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


class TorStatePy3Tests(unittest.TestCase):

    def setUp(self):
        self.protocol = TorControlProtocol()
        self.state = TorState(self.protocol)
        # avoid spew in trial logs; state prints this by default
        self.state._attacher_error = lambda f: f
        self.protocol.connectionMade = lambda: None
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)

    def send(self, line):
        self.protocol.dataReceived(line.strip() + b"\r\n")

    def test_attacher_coroutine(self):
        @implementer(IStreamAttacher)
        class MyAttacher(object):

            def __init__(self, answer):
                self.streams = []
                self.answer = answer

            async def attach_stream(self, stream, circuits):
                self.streams.append(stream)
                x = await defer.succeed(self.answer)
                return x

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
