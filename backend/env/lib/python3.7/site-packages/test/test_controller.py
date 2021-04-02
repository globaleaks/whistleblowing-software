import os
import functools
from os.path import join
from mock import Mock, patch
from six.moves import StringIO

from twisted.internet.interfaces import IReactorCore
from twisted.internet.interfaces import IListeningPort
from twisted.internet.interfaces import IStreamClientEndpoint
from twisted.internet.address import IPv4Address
from twisted.internet import defer, error, task
from twisted.python.failure import Failure
from twisted.trial import unittest
from twisted.test import proto_helpers

from txtorcon import TorConfig
from txtorcon import TorControlProtocol
from txtorcon import TorProcessProtocol
from txtorcon import launch
from txtorcon import connect
from txtorcon.controller import _is_non_public_numeric_address, Tor
from txtorcon.interface import ITorControlProtocol
from .util import TempDir

from zope.interface import implementer, directlyProvides


class FakeProcessTransport(proto_helpers.StringTransportWithDisconnection):
    pid = -1
    reactor = None

    def signalProcess(self, signame):
        assert self.reactor is not None
        self.reactor.callLater(
            0,
            lambda: self.process_protocol.processEnded(
                Failure(error.ProcessTerminated(signal=signame))
            )
        )
        self.reactor.callLater(
            0,
            lambda: self.process_protocol.processExited(
                Failure(error.ProcessTerminated(signal=signame))
            )
        )

    def closeStdin(self):
        self.process_protocol.outReceived(b"Bootstrap")
        return


class FakeProcessTransportNeverBootstraps(FakeProcessTransport):

    pid = -1

    def closeStdin(self):
        return


class FakeProcessTransportNoProtocol(FakeProcessTransport):
    def closeStdin(self):
        pass


@implementer(IListeningPort)
class FakePort(object):
    def __init__(self, port):
        self._port = port

    def startListening(self):
        pass

    def stopListening(self):
        pass

    def getHost(self):
        return IPv4Address('TCP', "127.0.0.1", self._port)


@implementer(IReactorCore)
class FakeReactor(task.Clock):

    def __init__(self, test, trans, on_protocol, listen_ports=[]):
        super(FakeReactor, self).__init__()
        self.test = test
        self.transport = trans
        self.transport.reactor = self  # XXX FIXME this is a cycle now
        self.on_protocol = on_protocol
        self.listen_ports = listen_ports
        # util.available_tcp_port ends up 'asking' for free ports via
        # listenTCP, ultimately, and the answers we send back are from
        # this list

    def spawnProcess(self, processprotocol, bin, args, env, path,
                     uid=None, gid=None, usePTY=None, childFDs=None):
        self.protocol = processprotocol
        self.protocol.makeConnection(self.transport)
        self.transport.process_protocol = processprotocol
        self.on_protocol(self.protocol)
        return self.transport

    def addSystemEventTrigger(self, *args):
        self.test.assertEqual(args[0], 'before')
        self.test.assertEqual(args[1], 'shutdown')
        # we know this is just for the temporary file cleanup, so we
        # nuke it right away to avoid polluting /tmp by calling the
        # callback now.
        args[2]()

    def removeSystemEventTrigger(self, id):
        pass

    def listenTCP(self, *args, **kw):
        port = self.listen_ports.pop()
        return FakePort(port)

    def connectTCP(self, host, port, factory, timeout=0, bindAddress=None):
        return

    def connectUNIX(self, *args, **kw):
        return


class LaunchTorTests(unittest.TestCase):

    def setUp(self):
        self.protocol = TorControlProtocol()
        self.protocol.connectionMade = lambda: None
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)
        self.clock = task.Clock()

    def test_ctor_timeout_no_ireactortime(self):
        with self.assertRaises(RuntimeError) as ctx:
            TorProcessProtocol(lambda: None, timeout=42)
        self.assertTrue("Must supply an IReactorTime" in str(ctx.exception))

    def _fake_queue(self, cmd):
        if cmd.split()[0] == 'PROTOCOLINFO':
            return defer.succeed('AUTH METHODS=NULL')
        elif cmd == 'GETINFO config/names':
            return defer.succeed('config/names=')
        elif cmd == 'GETINFO signal/names':
            return defer.succeed('signal/names=')
        elif cmd == 'GETINFO version':
            return defer.succeed('version=0.1.2.3')
        elif cmd == 'GETINFO events/names':
            return defer.succeed('events/names=STATUS_CLIENT')
        return defer.succeed(None)

    def _fake_event_listener(self, what, cb):
        if what == 'STATUS_CLIENT':
            # should ignore non-BOOTSTRAP messages
            cb('STATUS_CLIENT not-bootstrap')
            cb('STATUS_CLIENT BOOTSTRAP PROGRESS=100 TAG=foo SUMMARY=bar')
        return defer.succeed(None)

    @defer.inlineCallbacks
    def test_launch_tor_unix_controlport(self):
        trans = FakeProcessTransport()
        trans.protocol = self.protocol
        self.protocol.post_bootstrap.callback(self.protocol)
        self.protocol._set_valid_events("STATUS_CLIENT")
        self.protocol.add_event_listener = self._fake_event_listener
        self.protocol.queue_command = self._fake_queue

        def on_protocol(proto):
            proto.outReceived(b'Bootstrapped 90%\n')

        # launch() auto-discovers a SOCKS port
        reactor = FakeReactor(self, trans, on_protocol, [9050])
        reactor.connectUNIX = Mock()
        # prepare a suitable directory for tor unix socket
        with TempDir() as tmp:
            tmpdir = str(tmp)
            os.chmod(tmpdir, 0o0700)
            socket_file = join(tmpdir, 'test_socket_file')
            with patch('txtorcon.controller.UNIXClientEndpoint') as uce:
                endpoint = Mock()
                endpoint.connect = Mock(return_value=defer.succeed(self.protocol))
                uce.return_value = endpoint

                yield launch(
                    reactor,
                    control_port="unix:{}".format(socket_file),
                    tor_binary="/bin/echo",
                    stdout=Mock(),
                    stderr=Mock(),
                )

        self.assertTrue(endpoint.connect.called)
        self.assertTrue(uce.called)
        self.assertEqual(
            socket_file,
            uce.mock_calls[0][1][1],
        )

    @defer.inlineCallbacks
    def test_launch_tor_unix_controlport_wrong_perms(self):
        reactor = FakeReactor(self, Mock(), None, [9050])
        with self.assertRaises(ValueError) as ctx:
            with TempDir() as tmp:
                tmpdir = str(tmp)
                os.chmod(tmpdir, 0o0777)
                socket_file = join(tmpdir, 'socket_test')
                yield launch(
                    reactor,
                    control_port="unix:{}".format(socket_file),
                    tor_binary="/bin/echo",
                    stdout=Mock(),
                    stderr=Mock(),
                )
        self.assertTrue(
            "must only be readable by the user" in str(ctx.exception)
        )

    @defer.inlineCallbacks
    def test_launch_tor_unix_controlport_no_directory(self):
        reactor = FakeReactor(self, Mock(), None, [9050])
        with self.assertRaises(ValueError) as ctx:
            socket_file = '/does/not/exist'
            yield launch(
                reactor,
                control_port="unix:{}".format(socket_file),
                tor_binary="/bin/echo",
                stdout=Mock(),
                stderr=Mock(),
            )
        self.assertTrue("must exist" in str(ctx.exception))

    @patch('txtorcon.controller.find_tor_binary', return_value='/bin/echo')
    @defer.inlineCallbacks
    def test_launch_fails(self, ftb):
        trans = FakeProcessTransport()

        def on_proto(protocol):
            protocol.processEnded(
                Failure(error.ProcessTerminated(12, None, 'statusFIXME'))
            )
        reactor = FakeReactor(self, trans, on_proto, [1234, 9052])

        try:
            yield launch(reactor)
            self.fail("Should fail")
        except RuntimeError:
            pass

        errs = self.flushLoggedErrors(RuntimeError)
        self.assertEqual(1, len(errs))
        self.assertTrue(
            "Tor exited with error-code 12" in str(errs[0])
        )

    @defer.inlineCallbacks
    def test_launch_no_ireactorcore(self):
        try:
            yield launch(None)
            self.fail("should get exception")
        except ValueError as e:
            self.assertTrue("provide IReactorCore" in str(e))

    @patch('txtorcon.controller.find_tor_binary', return_value='/bin/echo')
    @patch('txtorcon.controller.TorProcessProtocol')
    @defer.inlineCallbacks
    def test_successful_launch(self, tpp, ftb):
        trans = FakeProcessTransport()
        reactor = FakeReactor(self, trans, lambda p: None, [1, 2, 3])
        config = TorConfig()

        def boot(arg=None):
            config.post_bootstrap.callback(config)
        config.__dict__['bootstrap'] = Mock(side_effect=boot)
        config.__dict__['attach_protocol'] = Mock(return_value=defer.succeed(None))

        def foo(*args, **kw):
            rtn = Mock()
            rtn.post_bootstrap = defer.succeed(None)
            rtn.when_connected = Mock(return_value=defer.succeed(rtn))
            return rtn
        tpp.side_effect = foo

        tor = yield launch(reactor, _tor_config=config)
        self.assertTrue(isinstance(tor, Tor))

    @defer.inlineCallbacks
    def test_quit(self):
        tor = Tor(Mock(), Mock())
        tor._protocol = Mock()
        tor._process_protocol = Mock()
        yield tor.quit()

    @defer.inlineCallbacks
    def test_quit_no_protocol(self):
        tor = Tor(Mock(), Mock())
        tor._protocol = None
        tor._process_protocol = None
        with self.assertRaises(RuntimeError) as ctx:
            yield tor.quit()
        self.assertTrue('no protocol instance' in str(ctx.exception))

    @patch('txtorcon.controller.socks')
    @defer.inlineCallbacks
    def test_dns_resolve(self, fake_socks):
        answer = object()
        cfg = Mock()
        proto = Mock()
        proto.get_conf = Mock(return_value=defer.succeed({"SocksPort": "9050"}))
        tor = Tor(Mock(), proto, _tor_config=cfg)
        fake_socks.resolve = Mock(return_value=defer.succeed(answer))
        ans = yield tor.dns_resolve("meejah.ca")
        self.assertEqual(ans, answer)

    @patch('txtorcon.controller.socks')
    @defer.inlineCallbacks
    def test_dns_resolve_existing_socks(self, fake_socks):
        answer = object()
        proto = Mock()
        proto.get_conf = Mock(return_value=defer.succeed({"SocksPort": "9050"}))
        tor = Tor(Mock(), proto)
        fake_socks.resolve = Mock(return_value=defer.succeed(answer))
        ans0 = yield tor.dns_resolve("meejah.ca")

        # do it again to exercise the _default_socks_port() case when
        # we already got the default
        fake_socks.resolve = Mock(return_value=defer.succeed(answer))
        ans1 = yield tor.dns_resolve("meejah.ca")
        self.assertEqual(ans0, answer)
        self.assertEqual(ans1, answer)

    @patch('txtorcon.controller.socks')
    @defer.inlineCallbacks
    def test_dns_resolve_no_configured_socks(self, fake_socks):
        answer = object()
        proto = Mock()
        proto.get_conf = Mock(return_value=defer.succeed({"SocksPort": "9050"}))
        cfg = Mock()
        tor = Tor(Mock(), proto, _tor_config=cfg)

        def boom(*args, **kw):
            raise RuntimeError("no socks")
        cfg.socks_endpoint = Mock(side_effect=boom)
        fake_socks.resolve = Mock(return_value=defer.succeed(answer))
        ans = yield tor.dns_resolve("meejah.ca")

        self.assertEqual(ans, answer)

    @patch('txtorcon.controller.socks')
    @defer.inlineCallbacks
    def test_dns_resolve_ptr(self, fake_socks):
        answer = object()
        proto = Mock()
        proto.get_conf = Mock(return_value=defer.succeed({"SocksPort": "9050"}))
        tor = Tor(Mock(), proto)
        fake_socks.resolve_ptr = Mock(return_value=defer.succeed(answer))
        ans = yield tor.dns_resolve_ptr("4.3.2.1")
        self.assertEqual(ans, answer)

    @patch('txtorcon.controller.find_tor_binary', return_value='/bin/echo')
    @defer.inlineCallbacks
    def test_successful_launch_tcp_control(self, ftb):
        """
        full end-to-end test of a launch, faking things out at a "lower
        level" than most of the other tests
        """
        trans = FakeProcessTransport()

        def on_protocol(proto):
            pass
        reactor = FakeReactor(self, trans, on_protocol, [1, 2, 3])

        def connect_tcp(host, port, factory, timeout=0, bindAddress=None):
            addr = Mock()
            factory.doStart()
            proto = factory.buildProtocol(addr)
            tpp = proto._wrappedProtocol
            tpp.add_event_listener = self._fake_event_listener
            tpp.queue_command = self._fake_queue
            proto.makeConnection(Mock())
            return proto
        reactor.connectTCP = connect_tcp

        config = TorConfig()

        tor = yield launch(reactor, _tor_config=config, control_port='1234', timeout=30)
        self.assertTrue(isinstance(tor, Tor))

    @patch('txtorcon.controller.find_tor_binary', return_value='/bin/echo')
    @patch('txtorcon.controller.sys')
    @patch('txtorcon.controller.TorProcessProtocol')
    @defer.inlineCallbacks
    def test_successful_launch_tcp_control_non_unix(self, tpp, _sys, ftb):
        _sys.platform = 'not darwin or linux2'
        trans = FakeProcessTransport()
        reactor = FakeReactor(self, trans, lambda p: None, [1, 2, 3])
        config = TorConfig()

        def boot(arg=None):
            config.post_bootstrap.callback(config)
        config.__dict__['bootstrap'] = Mock(side_effect=boot)
        config.__dict__['attach_protocol'] = Mock(return_value=defer.succeed(None))

        def foo(*args, **kw):
            rtn = Mock()
            rtn.post_bootstrap = defer.succeed(None)
            rtn.when_connected = Mock(return_value=defer.succeed(rtn))
            return rtn
        tpp.side_effect = foo

        tor = yield launch(reactor, _tor_config=config)
        self.assertTrue(isinstance(tor, Tor))

    @patch('txtorcon.controller.sys')
    @patch('txtorcon.controller.pwd')
    @patch('txtorcon.controller.os.geteuid')
    @patch('txtorcon.controller.os.chown')
    def test_launch_root_changes_tmp_ownership(self, chown, euid, _pwd, _sys):
        _pwd.return_value = 1000
        _sys.platform = 'linux2'
        euid.return_value = 0
        reactor = Mock()
        directlyProvides(reactor, IReactorCore)

        # note! we're providing enough options here that we react the
        # "chown" before any 'yield' statements in launch, so we don't
        # actually have to wait for it... a little rickety, though :/
        launch(reactor, tor_binary='/bin/echo', user='chuffington', socks_port='1234')
        self.assertEqual(1, chown.call_count)

    @defer.inlineCallbacks
    def test_launch_timeout_exception(self):
        """
        we provide a timeout, and it expires
        """
        trans = Mock()
        trans.signalProcess = Mock(side_effect=error.ProcessExitedAlready)
        trans.loseConnection = Mock()
        on_proto = Mock()
        react = FakeReactor(self, trans, on_proto, [1234])

        def creator():
            return defer.succeed(Mock())

        d = launch(
            reactor=react,
            tor_binary='/bin/echo',
            socks_port=1234,
            timeout=10,
            connection_creator=creator,
        )
        react.advance(12)
        self.assertTrue(trans.loseConnection.called)
        with self.assertRaises(RuntimeError) as ctx:
            yield d
        self.assertTrue("timeout while launching" in str(ctx.exception))

    @defer.inlineCallbacks
    def test_launch_timeout_process_exits(self):
        # cover the "one more edge case" where we get a processEnded()
        # but we've already "done" a timeout.
        trans = Mock()
        trans.signalProcess = Mock()
        trans.loseConnection = Mock()

        class MyFakeReactor(FakeReactor):
            def spawnProcess(self, processprotocol, bin, args, env, path,
                             uid=None, gid=None, usePTY=None, childFDs=None):
                self.protocol = processprotocol
                self.protocol.makeConnection(self.transport)
                self.transport.process_protocol = processprotocol
                self.on_protocol(self.protocol)

                status = Mock()
                status.value.exitCode = None
                processprotocol.processEnded(status)
                return self.transport

        react = MyFakeReactor(self, trans, Mock(), [1234, 9052])

        d = launch(
            reactor=react,
            tor_binary='/bin/echo',
            timeout=10,
            data_directory='/dev/null',
        )
        react.advance(20)

        try:
            yield d
        except RuntimeError as e:
            self.assertTrue("Tor was killed" in str(e))

        errs = self.flushLoggedErrors(RuntimeError)
        self.assertEqual(1, len(errs))
        self.assertTrue("Tor was killed" in str(errs[0]))

    @defer.inlineCallbacks
    def test_launch_wrong_stdout(self):
        try:
            yield launch(
                FakeReactor(self, Mock(), Mock()),
                stdout=object(),
                tor_binary='/bin/echo',
            )
            self.fail("Should have thrown an error")
        except RuntimeError as e:
            self.assertTrue("file-like object needed" in str(e).lower())

    @defer.inlineCallbacks
    def test_launch_with_timeout(self):
        # XXX not entirely sure what this was/is supposed to be
        # testing, but it covers an extra 7 lines of code??
        timeout = 5

        def connector(proto, trans):
            proto._set_valid_events('STATUS_CLIENT')
            proto.makeConnection(trans)
            proto.post_bootstrap.callback(proto)
            return proto.post_bootstrap

        def on_protocol(proto):
            proto.outReceived(b'Bootstrapped 100%\n')

        trans = FakeProcessTransportNeverBootstraps()
        trans.protocol = self.protocol
        creator = functools.partial(connector, Mock(), Mock())
        react = FakeReactor(self, trans, on_protocol, [1234, 9052])

        with self.assertRaises(RuntimeError) as ctx:
            d = launch(react, connection_creator=creator,
                       timeout=timeout, tor_binary='/bin/echo')
            # FakeReactor is a task.Clock subclass and +1 just to be sure
            react.advance(timeout + 1)
            yield d
        self.assertTrue(
            'timeout while launching Tor' in str(ctx.exception)
        )
        # could/should just use return from this to do asserts?
        self.flushLoggedErrors(RuntimeError)

    @defer.inlineCallbacks
    def test_tor_produces_stderr_output(self):
        def connector(proto, trans):
            proto._set_valid_events('STATUS_CLIENT')
            proto.makeConnection(trans)
            proto.post_bootstrap.callback(proto)
            return proto.post_bootstrap

        def on_protocol(proto):
            proto.errReceived('Something went horribly wrong!\n')

        trans = FakeProcessTransport()
        trans.protocol = Mock()
        fakeout = StringIO()
        fakeerr = StringIO()
        creator = functools.partial(connector, Mock(), Mock())
        try:
            yield launch(
                FakeReactor(self, trans, on_protocol, [1234, 9052]),
                connection_creator=creator,
                tor_binary='/bin/echo',
                stdout=fakeout,
                stderr=fakeerr,
            )
            self.fail()  # should't get callback
        except RuntimeError as e:
            self.assertEqual('', fakeout.getvalue())
            self.assertEqual('Something went horribly wrong!\n', fakeerr.getvalue())
            self.assertTrue(
                'Something went horribly wrong!' in str(e)
            )

    @patch('txtorcon.controller.find_tor_binary', return_value='/bin/echo')
    @defer.inlineCallbacks
    def test_tor_connection_fails(self, ftb):
        trans = FakeProcessTransport()

        def on_protocol(proto):
            proto.outReceived(b'Bootstrapped 100%\n')
        reactor = FakeReactor(self, trans, on_protocol, [1, 2, 3])

        fails = ['one']

        def connect_tcp(host, port, factory, timeout=0, bindAddress=None):
            if len(fails):
                fails.pop()
                raise error.CannotListenError('on-purpose-error', None, None)

            addr = Mock()
            factory.doStart()
            proto = factory.buildProtocol(addr)
            tpp = proto._wrappedProtocol

            def fake_event_listener(what, cb):
                if what == 'STATUS_CLIENT':
                    # should ignore non-BOOTSTRAP messages
                    cb('STATUS_CLIENT not-bootstrap')
                    cb('STATUS_CLIENT BOOTSTRAP PROGRESS=100 TAG=foo SUMMARY=bar')
                return defer.succeed(None)
            tpp.add_event_listener = fake_event_listener

            def fake_queue(cmd):
                if cmd.split()[0] == 'PROTOCOLINFO':
                    return defer.succeed('AUTH METHODS=NULL')
                elif cmd == 'GETINFO config/names':
                    return defer.succeed('config/names=')
                elif cmd == 'GETINFO signal/names':
                    return defer.succeed('signal/names=')
                elif cmd == 'GETINFO version':
                    return defer.succeed('version=0.1.2.3')
                elif cmd == 'GETINFO events/names':
                    return defer.succeed('events/names=STATUS_CLIENT')
                return defer.succeed(None)
            tpp.queue_command = fake_queue
            proto.makeConnection(Mock())
            return proto
        reactor.connectTCP = connect_tcp
        config = TorConfig()

        tor = yield launch(reactor, _tor_config=config, control_port='1234', timeout=30)
        errs = self.flushLoggedErrors()
        self.assertTrue(isinstance(tor, Tor))
        self.assertEqual(1, len(errs))

    def test_tor_connection_user_data_dir(self):
        """
        Test that we don't delete a user-supplied data directory.
        """

        config = TorConfig()
        config.OrPort = 1234

        class Connector:
            def __call__(self, proto, trans):
                proto._set_valid_events('STATUS_CLIENT')
                proto.makeConnection(trans)
                proto.post_bootstrap.callback(proto)
                return proto.post_bootstrap

        def on_protocol(proto):
            proto.outReceived(b'Bootstrapped 90%\n')

        with TempDir() as tmp:
            my_dir = str(tmp)
            config.DataDirectory = my_dir
            trans = FakeProcessTransport()
            trans.protocol = self.protocol
            creator = functools.partial(Connector(), self.protocol, self.transport)
            d = launch(
                FakeReactor(self, trans, on_protocol, [1234, 9051]),
                connection_creator=creator,
                tor_binary='/bin/echo',
                data_directory=my_dir,
                control_port=0,
            )

            def still_have_data_dir(tor, tester):
                tor._process_protocol.cleanup()  # FIXME? not really unit-testy as this is sort of internal function
                tester.assertTrue(os.path.exists(my_dir))

            d.addCallback(still_have_data_dir, self)
            d.addErrback(self.fail)
            return d

    def _test_tor_connection_user_control_port(self):
        """
        Confirm we use a user-supplied control-port properly
        """

        config = TorConfig()
        config.OrPort = 1234
        config.ControlPort = 4321

        class Connector:
            def __call__(self, proto, trans):
                proto._set_valid_events('STATUS_CLIENT')
                proto.makeConnection(trans)
                proto.post_bootstrap.callback(proto)
                return proto.post_bootstrap

        def on_protocol(proto):
            proto.outReceived(b'Bootstrapped 90%\n')
            proto.outReceived(b'Bootstrapped 100%\n')

        trans = FakeProcessTransport()
        trans.protocol = self.protocol
        creator = functools.partial(Connector(), self.protocol, self.transport)
        d = launch(
            FakeReactor(self, trans, on_protocol, [9052]),
            connection_creator=creator,
            tor_binary='/bin/echo',
            socks_port=1234,
        )

        def check_control_port(proto, tester):
            # we just want to ensure launch() didn't mess with
            # the controlport we set
            tester.assertEqual(config.ControlPort, 4321)

        d.addCallback(check_control_port, self)
        d.addErrback(self.fail)
        return d

    @defer.inlineCallbacks
    def _test_tor_connection_default_control_port(self):
        """
        Confirm a default control-port is set if not user-supplied.
        """

        class Connector:
            def __call__(self, proto, trans):
                proto._set_valid_events('STATUS_CLIENT')
                proto.makeConnection(trans)
                proto.post_bootstrap.callback(proto)
                return proto.post_bootstrap

        def on_protocol(proto):
            proto.outReceived(b'Bootstrapped 90%\n')
            proto.outReceived(b'Bootstrapped 100%\n')

        trans = FakeProcessTransport()
        trans.protocol = self.protocol
        creator = functools.partial(Connector(), self.protocol, self.transport)
        tor = yield launch(
            FakeReactor(self, trans, on_protocol, [9052]),
            connection_creator=creator,
            tor_binary='/bin/echo',
            socks_port=1234,
        )

        cfg = yield tor.get_config()
        self.assertEqual(cfg.ControlPort, 9052)

    def test_progress_updates(self):
        self.got_progress = False

        def confirm_progress(p, t, s):
            self.assertEqual(p, 10)
            self.assertEqual(t, 'tag')
            self.assertEqual(s, 'summary')
            self.got_progress = True
        process = TorProcessProtocol(None, confirm_progress)
        process.progress(10, 'tag', 'summary')
        self.assertTrue(self.got_progress)

    def test_quit_process(self):
        process = TorProcessProtocol(None)
        process.transport = Mock()

        d = process.quit()
        self.assertFalse(d.called)

        process.processExited(Failure(error.ProcessTerminated(exitCode=15)))
        self.assertTrue(d.called)
        process.processEnded(Failure(error.ProcessDone(None)))
        self.assertTrue(d.called)
        errs = self.flushLoggedErrors()
        self.assertEqual(1, len(errs))
        self.assertTrue("Tor exited with error-code" in str(errs[0]))

    def test_quit_process_already(self):
        process = TorProcessProtocol(None)
        process.transport = Mock()

        def boom(sig):
            self.assertEqual(sig, 'TERM')
            raise error.ProcessExitedAlready()
        process.transport.signalProcess = Mock(side_effect=boom)

        d = process.quit()
        process.processEnded(Failure(error.ProcessDone(None)))
        self.assertTrue(d.called)
        errs = self.flushLoggedErrors()
        self.assertEqual(1, len(errs))
        self.assertTrue("Tor exited with error-code" in str(errs[0]))

    @defer.inlineCallbacks
    def test_quit_process_error(self):
        process = TorProcessProtocol(None)
        process.transport = Mock()

        def boom(sig):
            self.assertEqual(sig, 'TERM')
            raise RuntimeError("Something bad")
        process.transport.signalProcess = Mock(side_effect=boom)

        try:
            yield process.quit()
        except RuntimeError as e:
            self.assertEqual("Something bad", str(e))

    def XXXtest_status_updates(self):
        process = TorProcessProtocol(None)
        process.status_client("NOTICE CONSENSUS_ARRIVED")

    def XXXtest_tor_launch_success_then_shutdown(self):
        """
        There was an error where we double-callbacked a deferred,
        i.e. success and then shutdown. This repeats it.
        """
        process = TorProcessProtocol(None)
        process.status_client(
            'STATUS_CLIENT BOOTSTRAP PROGRESS=100 TAG=foo SUMMARY=cabbage'
        )
        # XXX why this assert?
        self.assertEqual(None, process._connected_cb)

        class Value(object):
            exitCode = 123

        class Status(object):
            value = Value()
        process.processEnded(Status())
        self.assertEqual(len(self.flushLoggedErrors(RuntimeError)), 1)

    @defer.inlineCallbacks
    def test_launch_no_control_port(self):
        '''
        See Issue #80. This allows you to launch tor with a TorConfig
        with ControlPort=0 in case you don't want a control connection
        at all. In this case you get back a TorProcessProtocol and you
        own both pieces. (i.e. you have to kill it yourself).
        '''

        trans = FakeProcessTransportNoProtocol()
        trans.protocol = self.protocol

        def creator(*args, **kw):
            print("Bad: connection creator called")
            self.fail()

        def on_protocol(proto):
            self.process_proto = proto
            proto.outReceived(b'Bootstrapped 90%\n')
            proto.outReceived(b'Bootstrapped 100%\n')

        reactor = FakeReactor(self, trans, on_protocol, [9052, 9999])

        tor = yield launch(
            reactor=reactor,
            connection_creator=creator,
            tor_binary='/bin/echo',
            socks_port=1234,
            control_port=0,
        )
        self.assertEqual(tor._process_protocol, self.process_proto)
        d = tor.quit()
        reactor.advance(0)
        yield d
        errs = self.flushLoggedErrors()
        self.assertEqual(1, len(errs))
        self.assertTrue("Tor was killed" in str(errs[0]))


def create_endpoint(*args, **kw):
    ep = Mock()
    directlyProvides(ep, IStreamClientEndpoint)
    return ep


def create_endpoint_fails(*args, **kw):
    def go_boom(*args, **kw):
        raise RuntimeError("boom")

    ep = Mock(side_effect=go_boom)
    directlyProvides(ep, IStreamClientEndpoint)
    return ep


class ConnectTorTests(unittest.TestCase):

    @patch('txtorcon.controller.TorConfig')
    @patch('txtorcon.controller.UNIXClientEndpoint', side_effect=create_endpoint)
    @patch('txtorcon.controller.TCP4ClientEndpoint', side_effect=create_endpoint)
    @defer.inlineCallbacks
    def test_connect_defaults(self, fake_cfg, fake_unix, fake_tcp):
        """
        happy-path test, ensuring there are no exceptions
        """
        transport = Mock()
        reactor = FakeReactor(self, transport, lambda: None)
        yield connect(reactor)

    @patch('txtorcon.controller.TorConfig')
    @defer.inlineCallbacks
    def test_connect_provide_endpoint(self, fake_cfg):
        transport = Mock()
        reactor = FakeReactor(self, transport, lambda: None)
        ep = Mock()
        with self.assertRaises(ValueError) as ctx:
            yield connect(reactor, ep)
        self.assertTrue('IStreamClientEndpoint' in str(ctx.exception))

    @patch('txtorcon.controller.TorConfig')
    @defer.inlineCallbacks
    def test_connect_provide_multiple_endpoints(self, fake_cfg):
        transport = Mock()
        reactor = FakeReactor(self, transport, lambda: None)
        ep0 = Mock()
        ep1 = Mock()
        with self.assertRaises(ValueError) as ctx:
            yield connect(reactor, [ep0, ep1])
        self.assertTrue('IStreamClientEndpoint' in str(ctx.exception))

    @patch('txtorcon.controller.TorConfig')
    @defer.inlineCallbacks
    def test_connect_multiple_endpoints_error(self, fake_cfg):
        transport = Mock()
        reactor = FakeReactor(self, transport, lambda: None)
        ep0 = Mock()

        def boom(*args, **kw):
            raise RuntimeError("the bad thing")
        ep0.connect = boom
        directlyProvides(ep0, IStreamClientEndpoint)
        with self.assertRaises(RuntimeError) as ctx:
            yield connect(reactor, ep0)
        self.assertEqual("the bad thing", str(ctx.exception))

    @patch('txtorcon.controller.TorConfig')
    @defer.inlineCallbacks
    def test_connect_multiple_endpoints_many_errors(self, fake_cfg):
        transport = Mock()
        reactor = FakeReactor(self, transport, lambda: None)
        ep0 = Mock()
        ep1 = Mock()

        def boom0(*args, **kw):
            raise RuntimeError("the bad thing")

        def boom1(*args, **kw):
            raise RuntimeError("more sadness")

        ep0.connect = boom0
        ep1.connect = boom1
        directlyProvides(ep0, IStreamClientEndpoint)
        directlyProvides(ep1, IStreamClientEndpoint)

        with self.assertRaises(RuntimeError) as ctx:
            yield connect(reactor, [ep0, ep1])
        self.assertTrue("the bad thing" in str(ctx.exception))
        self.assertTrue("more sadness" in str(ctx.exception))

    @patch('txtorcon.controller.TorConfig')
    @defer.inlineCallbacks
    def test_connect_success(self, fake_cfg):
        transport = Mock()
        reactor = FakeReactor(self, transport, lambda: None)
        torcfg = Mock()
        fake_cfg.from_protocol = Mock(return_value=torcfg)
        ep0 = Mock()
        proto = object()
        torcfg.protocol = proto
        ep0.connect = Mock(return_value=proto)
        directlyProvides(ep0, IStreamClientEndpoint)

        ans = yield connect(reactor, [ep0])
        cfg = yield ans.get_config()
        self.assertEqual(cfg, torcfg)
        self.assertEqual(ans.protocol, proto)


class WebAgentTests(unittest.TestCase):

    def setUp(self):
        proto = Mock()
        self.pool = Mock()
        self.expected_response = object()
        proto.request = Mock(return_value=defer.succeed(self.expected_response))
        self.pool.getConnection = Mock(return_value=defer.succeed(proto))

    @defer.inlineCallbacks
    def test_web_agent_defaults(self):
        reactor = Mock()
        # XXX is there a faster way to do this? better reactor fake?
        fake_host = Mock()
        fake_host.port = 1234
        fake_port = Mock()
        fake_port.getHost = Mock(return_value=fake_host)
        reactor.listenTCP = Mock(return_value=fake_port)
        cfg = Mock()
        cfg.create_socks_endpoint = Mock(return_value=defer.succeed("9050"))
        proto = Mock()
        proto.get_conf = Mock(return_value=defer.succeed({}))
        directlyProvides(proto, ITorControlProtocol)

        tor = Tor(reactor, proto, _tor_config=cfg)
        try:
            agent = tor.web_agent(pool=self.pool)
        except ImportError as e:
            if 'IAgentEndpointFactory' in str(e):
                print("Skipping; appears we don't have web support")
                return

        resp = yield agent.request('GET', b'meejah.ca')
        self.assertEqual(self.expected_response, resp)

    @defer.inlineCallbacks
    def test_web_agent_deferred(self):
        socks_d = defer.succeed("9151")
        reactor = Mock()
        cfg = Mock()
        proto = Mock()
        directlyProvides(proto, ITorControlProtocol)

        tor = Tor(reactor, proto, _tor_config=cfg)
        agent = tor.web_agent(pool=self.pool, socks_endpoint=socks_d)

        resp = yield agent.request('GET', b'meejah.ca')
        self.assertEqual(self.expected_response, resp)

    @defer.inlineCallbacks
    def test_web_agent_endpoint(self):
        socks = Mock()
        directlyProvides(socks, IStreamClientEndpoint)
        reactor = Mock()
        cfg = Mock()
        proto = Mock()
        directlyProvides(proto, ITorControlProtocol)

        tor = Tor(reactor, proto, _tor_config=cfg)
        agent = tor.web_agent(pool=self.pool, socks_endpoint=socks)

        resp = yield agent.request('GET', b'meejah.ca')
        self.assertEqual(self.expected_response, resp)

    @defer.inlineCallbacks
    def test_web_agent_error(self):
        reactor = Mock()
        cfg = Mock()
        proto = Mock()
        directlyProvides(proto, ITorControlProtocol)

        tor = Tor(reactor, proto, _tor_config=cfg)
        with self.assertRaises(ValueError) as ctx:
            agent = tor.web_agent(pool=self.pool, socks_endpoint=object())
            yield agent.request('GET', b'meejah.ca')
        self.assertTrue("'socks_endpoint' should be" in str(ctx.exception))


class TorAttributeTests(unittest.TestCase):

    def setUp(self):
        reactor = Mock()
        proto = Mock()
        directlyProvides(proto, ITorControlProtocol)
        self.cfg = Mock()
        self.tor = Tor(reactor, proto, _tor_config=self.cfg)

    def test_process(self):
        with self.assertRaises(Exception) as ctx:
            self.tor.process
        self.assertTrue('not launched by us' in str(ctx.exception))

    def test_when_connected_already(self):
        tpp = TorProcessProtocol(lambda: None)
        # hmmmmmph, delving into internal state "because way shorter
        # test"
        tpp._connected_listeners = None
        d = tpp.when_connected()

        self.assertTrue(d.called)
        self.assertEqual(d.result, tpp)

    def test_process_exists(self):
        gold = object()
        self.tor._process_protocol = gold
        self.assertEqual(gold, self.tor.process)

    def test_protocol_exists(self):
        self.tor.protocol

    def test_version_passthrough(self):
        self.tor.version


class TorAttributeTestsNoConfig(unittest.TestCase):

    def setUp(self):
        reactor = Mock()
        proto = Mock()
        directlyProvides(proto, ITorControlProtocol)
        self.tor = Tor(reactor, proto)

    @defer.inlineCallbacks
    def test_get_config(self):
        with patch('txtorcon.controller.TorConfig') as torcfg:
            gold = object()
            torcfg.from_protocol = Mock(return_value=defer.succeed(gold))
            cfg = yield self.tor.get_config()
            self.assertEqual(gold, cfg)


class TorStreamTests(unittest.TestCase):

    def setUp(self):
        reactor = Mock()
        proto = Mock()
        proto.get_conf = Mock(return_value=defer.succeed({"SocksPort": "9050"}))
        self.cfg = Mock()
        self.tor = Tor(reactor, proto, _tor_config=self.cfg)

    def test_sanity(self):
        self.assertTrue(_is_non_public_numeric_address(u'10.0.0.0'))
        self.assertTrue(_is_non_public_numeric_address(u'::1'))

    def test_v6(self):
        import ipaddress
        ipaddress.ip_address(u'2603:3023:807:3d00:21e:52ff:fe71:a4ce')

    def test_stream_private_ip(self):
        with self.assertRaises(Exception) as ctx:
            self.tor.stream_via('10.0.0.1', '1234')
        self.assertTrue("isn't going to work over Tor", str(ctx.exception))

    def test_stream_v6(self):
        with self.assertRaises(Exception) as ctx:
            self.tor.stream_via(u'::1', '1234')
        self.assertTrue("isn't going to work over Tor", str(ctx.exception))

    def test_public_v6(self):
        # should not be an error
        self.tor.stream_via(u'2603:3023:807:3d00:21e:52ff:fe71:a4ce', '4321')

    def test_public_v4(self):
        # should not be an error
        self.tor.stream_via(u'8.8.8.8', '4321')

    def test_stream_host(self):
        self.tor.stream_via(b'meejah.ca', '1234')


class IteratorTests(unittest.TestCase):
    def XXXtest_iterate_torconfig(self):
        cfg = TorConfig()
        cfg.FooBar = 'quux'
        cfg.save()
        cfg.Quux = 'blimblam'

        keys = sorted([k for k in cfg])

        self.assertEqual(['FooBar', 'Quux'], keys)


class FactoryFunctionTests(unittest.TestCase):
    """
    Mostly simple 'does not blow up' sanity checks of simple
    factory-functions.
    """

    @defer.inlineCallbacks
    def test_create_state(self):
        tor = Tor(Mock(), Mock())
        with patch('txtorcon.controller.TorState') as ts:
            ts.post_boostrap = defer.succeed('boom')
            yield tor.create_state()
        # no assertions; we just testing this doesn't raise

    def test_str(self):
        tor = Tor(Mock(), Mock())
        str(tor)
        # just testing the __str__ method doesn't explode
