from __future__ import print_function
from __future__ import with_statement

from os.path import exists

from twisted.python import log, failure
from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet import defer, error

from txtorcon import TorControlProtocol, TorProtocolFactory, TorState
from txtorcon import ITorControlProtocol
from txtorcon.torcontrolprotocol import parse_keywords, DEFAULT_VALUE
from txtorcon.util import hmac_sha256

import functools
import tempfile
import base64
from binascii import b2a_hex, a2b_hex


class CallbackChecker:
    def __init__(self, expected):
        self.expected_value = expected
        self.called_back = False

    def __call__(self, *args, **kwargs):
        v = args[0]
        if v != self.expected_value:
            print("WRONG")
            raise RuntimeError(
                'Expected "%s" but got "%s"' % (self.expected_value, v)
            )
        self.called_back = True
        return v


class InterfaceTests(unittest.TestCase):
    def test_implements(self):
        self.assertTrue(ITorControlProtocol.implementedBy(TorControlProtocol))

    def test_object_implements(self):
        self.assertTrue(ITorControlProtocol.providedBy(TorControlProtocol()))


class LogicTests(unittest.TestCase):

    def setUp(self):
        self.protocol = TorControlProtocol()
        self.protocol.connectionMade = lambda: None
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)

    def test_set_conf_wrong_args(self):
        ctl = TorControlProtocol()
        d = ctl.set_conf('a')
        self.assertTrue(d.called)
        self.assertTrue(d.result)
        self.assertTrue('even number' in d.result.getErrorMessage())
        # ignore the error so trial doesn't get unhappy
        d.addErrback(lambda foo: True)
        return d


class FactoryTests(unittest.TestCase):
    def test_create(self):
        TorProtocolFactory().buildProtocol(None)


class AuthenticationTests(unittest.TestCase):

    def setUp(self):
        self.protocol = TorControlProtocol()
        self.transport = proto_helpers.StringTransport()

    def send(self, line):
        assert type(line) == bytes
        self.protocol.dataReceived(line.strip() + b"\r\n")

    def test_authenticate_cookie(self):
        self.protocol.makeConnection(self.transport)
        self.assertEqual(self.transport.value(), b'PROTOCOLINFO 1\r\n')
        self.transport.clear()
        cookie_data = b'cookiedata!cookiedata!cookiedata'
        with open('authcookie', 'wb') as f:
            f.write(cookie_data)
        self.send(b'250-PROTOCOLINFO 1')
        self.send(b'250-AUTH METHODS=COOKIE,HASHEDPASSWORD COOKIEFILE="authcookie"')
        self.send(b'250-VERSION Tor="0.2.2.34"')
        self.send(b'250 OK')

        self.assertEqual(
            self.transport.value(),
            b'AUTHENTICATE ' + b2a_hex(cookie_data) + b'\r\n',
        )

    def test_authenticate_password(self):
        self.protocol.password_function = lambda: 'foo'
        self.protocol.makeConnection(self.transport)
        self.assertEqual(self.transport.value(), b'PROTOCOLINFO 1\r\n')
        self.transport.clear()
        self.send(b'250-PROTOCOLINFO 1')
        self.send(b'250-AUTH METHODS=HASHEDPASSWORD')
        self.send(b'250-VERSION Tor="0.2.2.34"')
        self.send(b'250 OK')

        self.assertEqual(
            self.transport.value(),
            b'AUTHENTICATE ' + b2a_hex(b'foo') + b'\r\n'
        )

    def test_authenticate_password_not_bytes(self):
        self.protocol.password_function = lambda: u'foo'
        self.protocol.makeConnection(self.transport)
        self.assertEqual(self.transport.value(), b'PROTOCOLINFO 1\r\n')
        self.transport.clear()
        self.send(b'250-PROTOCOLINFO 1')
        self.send(b'250-AUTH METHODS=HASHEDPASSWORD')
        self.send(b'250-VERSION Tor="0.2.2.34"')
        self.send(b'250 OK')

        self.assertEqual(
            self.transport.value(),
            b'AUTHENTICATE ' + b2a_hex(b'foo') + b'\r\n'
        )

    def test_authenticate_null(self):
        self.protocol.makeConnection(self.transport)
        self.assertEqual(self.transport.value(), b'PROTOCOLINFO 1\r\n')
        self.transport.clear()
        self.send(b'250-PROTOCOLINFO 1')
        self.send(b'250-AUTH METHODS=NULL')
        self.send(b'250-VERSION Tor="0.2.2.34"')
        self.send(b'250 OK')

        self.assertEqual(self.transport.value(), b'AUTHENTICATE\r\n')

    def test_authenticate_password_deferred(self):
        d = defer.Deferred()
        self.protocol.password_function = lambda: d
        self.protocol.makeConnection(self.transport)
        self.assertEqual(self.transport.value(), b'PROTOCOLINFO 1\r\n')
        self.transport.clear()
        self.send(b'250-PROTOCOLINFO 1')
        self.send(b'250-AUTH METHODS=HASHEDPASSWORD')
        self.send(b'250-VERSION Tor="0.2.2.34"')
        self.send(b'250 OK')

        # make sure we haven't tried to authenticate before getting
        # the password callback
        self.assertEqual(self.transport.value(), b'')
        d.callback('foo')

        # now make sure we DID try to authenticate
        self.assertEqual(
            self.transport.value(),
            b'AUTHENTICATE ' + b2a_hex(b"foo") + b'\r\n'
        )

    def test_authenticate_password_deferred_but_no_password(self):
        d = defer.Deferred()
        self.protocol.password_function = lambda: d
        self.protocol.makeConnection(self.transport)
        self.assertEqual(self.transport.value(), b'PROTOCOLINFO 1\r\n')
        self.transport.clear()
        self.send(b'250-PROTOCOLINFO 1')
        self.send(b'250-AUTH METHODS=HASHEDPASSWORD')
        self.send(b'250-VERSION Tor="0.2.2.34"')
        self.send(b'250 OK')
        d.callback(None)
        return self.assertFailure(self.protocol.post_bootstrap, RuntimeError)

    def confirmAuthFailed(self, *args):
        self.auth_failed = True

    def test_authenticate_no_password(self):
        self.protocol.post_bootstrap.addErrback(self.confirmAuthFailed)
        self.auth_failed = False

        self.protocol.makeConnection(self.transport)
        self.assertEqual(self.transport.value(), b'PROTOCOLINFO 1\r\n')

        self.send(b'250-PROTOCOLINFO 1')
        self.send(b'250-AUTH METHODS=HASHEDPASSWORD')
        self.send(b'250-VERSION Tor="0.2.2.34"')
        self.send(b'250 OK')

        self.assertTrue(self.auth_failed)


class DisconnectionTests(unittest.TestCase):
    def setUp(self):
        self.protocol = TorControlProtocol()
        self.protocol.connectionMade = lambda: None
        self.transport = proto_helpers.StringTransportWithDisconnection()
        self.protocol.makeConnection(self.transport)
        # why doesn't makeConnection do this?
        self.transport.protocol = self.protocol

    def tearDown(self):
        self.protocol = None

    def test_disconnect_callback(self):
        """
        see that we get our callback on_disconnect if the transport
        goes away
        """
        def it_was_called(*args):
            it_was_called.yes = True
            return None
        it_was_called.yes = False
        self.protocol.on_disconnect.addCallback(it_was_called)
        self.protocol.on_disconnect.addErrback(it_was_called)
        f = failure.Failure(error.ConnectionDone("It's all over"))
        self.protocol.connectionLost(f)
        self.assertTrue(it_was_called.yes)

    def test_disconnect_errback(self):
        """
        see that we get our callback on_disconnect if the transport
        goes away
        """
        def it_was_called(*args):
            it_was_called.yes = True
            return None
        it_was_called.yes = False
        self.protocol.on_disconnect.addCallback(it_was_called)
        self.protocol.on_disconnect.addErrback(it_was_called)
        f = failure.Failure(RuntimeError("The thing didn't do the stuff."))
        self.protocol.connectionLost(f)
        self.assertTrue(it_was_called.yes)


class ProtocolTests(unittest.TestCase):

    def setUp(self):
        self.protocol = TorControlProtocol()
        self.protocol.connectionMade = lambda: None
        self.transport = proto_helpers.StringTransport()
        self.protocol.makeConnection(self.transport)

    def tearDown(self):
        self.protocol = None

    def send(self, line):
        assert type(line) == bytes
        self.protocol.dataReceived(line.strip() + b"\r\n")

    def test_statemachine_broadcast_no_code(self):
        try:
            self.protocol._broadcast_response("foo")
            self.fail()
        except RuntimeError as e:
            self.assertTrue('No code set yet' in str(e))

    def test_statemachine_broadcast_unknown_code(self):
        try:
            self.protocol.code = 999
            self.protocol._broadcast_response("foo")
            self.fail()
        except RuntimeError as e:
            self.assertTrue('Unknown code' in str(e))

    def test_statemachine_is_finish(self):
        self.assertTrue(not self.protocol._is_finish_line(''))
        self.assertTrue(self.protocol._is_finish_line('.'))
        self.assertTrue(self.protocol._is_finish_line('300 '))
        self.assertTrue(not self.protocol._is_finish_line('250-'))

    def test_statemachine_singleline(self):
        self.assertTrue(not self.protocol._is_single_line_response('foo'))

    def test_statemachine_continuation(self):
        try:
            self.protocol.code = 250
            self.protocol._is_continuation_line("123 ")
            self.fail()
        except RuntimeError as e:
            self.assertTrue('Unexpected code' in str(e))

    def test_statemachine_multiline(self):
        try:
            self.protocol.code = 250
            self.protocol._is_multi_line("123 ")
            self.fail()
        except RuntimeError as e:
            self.assertTrue('Unexpected code' in str(e))

    def test_response_with_no_request(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.protocol.code = 200
            self.protocol._broadcast_response('200 OK')
        self.assertTrue(
            "didn't issue a command" in str(ctx.exception)
        )

    def auth_failed(self, msg):
        self.assertEqual(str(msg.value), '551 go away')
        self.got_auth_failed = True

    def test_authenticate_fail(self):
        self.got_auth_failed = False
        self.protocol._auth_failed = self.auth_failed

        self.protocol.password_function = lambda: 'foo'
        self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=HASHEDPASSWORD
VERSION Tor="0.2.2.35"
OK''')
        self.send(b'551 go away\r\n')
        self.assertTrue(self.got_auth_failed)

    def test_authenticate_no_auth_line(self):
        try:
            self.protocol._do_authenticate('''PROTOCOLINFO 1
FOOAUTH METHODS=COOKIE,SAFECOOKIE COOKIEFILE="/dev/null"
VERSION Tor="0.2.2.35"
OK''')
            self.assertTrue(False)
        except RuntimeError as e:
            self.assertTrue('find AUTH line' in str(e))

    def test_authenticate_not_enough_cookie_data(self):
        with tempfile.NamedTemporaryFile() as cookietmp:
            cookietmp.write(b'x' * 35)  # too much data
            cookietmp.flush()

            try:
                self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=COOKIE COOKIEFILE="%s"
VERSION Tor="0.2.2.35"
OK''' % cookietmp.name)
                self.assertTrue(False)
            except RuntimeError as e:
                self.assertTrue('cookie to be 32' in str(e))

    def test_authenticate_not_enough_safecookie_data(self):
        with tempfile.NamedTemporaryFile() as cookietmp:
            cookietmp.write(b'x' * 35)  # too much data
            cookietmp.flush()

            try:
                self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=SAFECOOKIE COOKIEFILE="%s"
VERSION Tor="0.2.2.35"
OK''' % cookietmp.name)
                self.assertTrue(False)
            except RuntimeError as e:
                self.assertTrue('cookie to be 32' in str(e))

    def test_authenticate_safecookie(self):
        with tempfile.NamedTemporaryFile() as cookietmp:
            cookiedata = bytes(bytearray([0] * 32))
            cookietmp.write(cookiedata)
            cookietmp.flush()

            self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=SAFECOOKIE COOKIEFILE="{}"
VERSION Tor="0.2.2.35"
OK'''.format(cookietmp.name))
            self.assertTrue(
                b'AUTHCHALLENGE SAFECOOKIE ' in self.transport.value()
            )
            x = self.transport.value().split()[-1]
            client_nonce = a2b_hex(x)
            self.transport.clear()
            server_nonce = bytes(bytearray([0] * 32))
            server_hash = hmac_sha256(
                b"Tor safe cookie authentication server-to-controller hash",
                cookiedata + client_nonce + server_nonce,
            )

            self.send(
                b'250 AUTHCHALLENGE SERVERHASH=' +
                base64.b16encode(server_hash) + b' SERVERNONCE=' +
                base64.b16encode(server_nonce) + b'\r\n'
            )
            self.assertTrue(b'AUTHENTICATE ' in self.transport.value())

    def test_authenticate_cookie_without_reading(self):
        server_nonce = bytes(bytearray([0] * 32))
        server_hash = bytes(bytearray([0] * 32))
        try:
            self.protocol._safecookie_authchallenge(
                '250 AUTHCHALLENGE SERVERHASH=%s SERVERNONCE=%s' %
                (base64.b16encode(server_hash), base64.b16encode(server_nonce))
            )
            self.assertTrue(False)
        except RuntimeError as e:
            self.assertTrue('not read' in str(e))

    def test_authenticate_unexisting_cookie_file(self):
        unexisting_file = __file__ + "-unexisting"
        try:
            self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=COOKIE COOKIEFILE="%s"
VERSION Tor="0.2.2.35"
OK''' % unexisting_file)
            self.assertTrue(False)
        except RuntimeError:
            pass

    def test_authenticate_unexisting_safecookie_file(self):
        unexisting_file = __file__ + "-unexisting"
        try:
            self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=SAFECOOKIE COOKIEFILE="{}"
VERSION Tor="0.2.2.35"
OK'''.format(unexisting_file))
            self.assertTrue(False)
        except RuntimeError:
            pass

    def test_authenticate_dont_send_cookiefile(self):
        try:
            self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=SAFECOOKIE
VERSION Tor="0.2.2.35"
OK''')
            self.assertTrue(False)
        except RuntimeError:
            pass

    def test_authenticate_password_when_cookie_unavailable(self):
        unexisting_file = __file__ + "-unexisting"
        self.protocol.password_function = lambda: 'foo'
        self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=COOKIE,HASHEDPASSWORD COOKIEFILE="{}"
VERSION Tor="0.2.2.35"
OK'''.format(unexisting_file))
        self.assertEqual(
            self.transport.value(),
            b'AUTHENTICATE ' + b2a_hex(b'foo') + b'\r\n',
        )

    def test_authenticate_password_when_safecookie_unavailable(self):
        unexisting_file = __file__ + "-unexisting"
        self.protocol.password_function = lambda: 'foo'
        self.protocol._do_authenticate('''PROTOCOLINFO 1
AUTH METHODS=SAFECOOKIE,HASHEDPASSWORD COOKIEFILE="{}"
VERSION Tor="0.2.2.35"
OK'''.format(unexisting_file))
        self.assertEqual(
            self.transport.value(),
            b'AUTHENTICATE ' + b2a_hex(b'foo') + b'\r\n',
        )

    def test_authenticate_safecookie_wrong_hash(self):
        cookiedata = bytes(bytearray([0] * 32))
        server_nonce = bytes(bytearray([0] * 32))
        server_hash = bytes(bytearray([0] * 32))

        # pretend we already did PROTOCOLINFO and read the cookie
        # file
        self.protocol._cookie_data = cookiedata
        self.protocol.client_nonce = server_nonce  # all 0's anyway
        try:
            self.protocol._safecookie_authchallenge(
                '250 AUTHCHALLENGE SERVERHASH={} SERVERNONCE={}'.format(
                    b2a_hex(server_hash).decode('ascii'),
                    b2a_hex(server_nonce).decode('ascii'),
                )
            )
            self.assertTrue(False)
        except RuntimeError as e:
            self.assertTrue('hash not expected' in str(e))

    def confirm_version_events(self, arg):
        self.assertEqual(self.protocol.version, 'foo')
        events = 'GUARD STREAM CIRC NS NEWCONSENSUS ORCONN NEWDESC ADDRMAP STATUS_GENERAL'.split()
        self.assertEqual(len(self.protocol.valid_events), len(events))
        self.assertTrue(all(x in self.protocol.valid_events for x in events))

    def test_bootstrap_callback(self):
        d = self.protocol.post_bootstrap
        d.addCallback(CallbackChecker(self.protocol))
        d.addCallback(self.confirm_version_events)

        events = b'GUARD STREAM CIRC NS NEWCONSENSUS ORCONN NEWDESC ADDRMAP STATUS_GENERAL'
        self.protocol._bootstrap()

        # answer all the requests generated by boostrapping etc.
        self.send(b"250-signal/names=")
        self.send(b"250 OK")

        self.send(b"250-version=foo")
        self.send(b"250 OK")

        self.send(b"250-events/names=" + events)
        self.send(b"250 OK")

        self.send(b"250 OK")  # for USEFEATURE

        return d

    def test_bootstrap_tor_does_not_support_signal_names(self):
        self.protocol._bootstrap()
        self.send(b'552 Unrecognized key "signal/names"')
        valid_signals = ["RELOAD", "DUMP", "DEBUG", "NEWNYM", "CLEARDNSCACHE"]
        self.assertEqual(self.protocol.valid_signals, valid_signals)

    def test_async(self):
        """
        test the example from control-spec.txt to see that we
        handle interleaved async notifications properly.
        """
        self.protocol._set_valid_events('CIRC')
        self.protocol.add_event_listener('CIRC', lambda _: None)
        self.send(b"250 OK")

        d = self.protocol.get_conf("SOCKSPORT ORPORT")
        self.send(b"650 CIRC 1000 EXTENDED moria1,moria2")
        self.send(b"250-SOCKSPORT=9050")
        self.send(b"250 ORPORT=0")
        return d

    def test_async_multiline(self):
        # same as above, but i think the 650's can be multline,
        # too. Like:
        # 650-CIRC 1000 EXTENDED moria1,moria2 0xBEEF
        # 650-EXTRAMAGIC=99
        # 650 ANONYMITY=high

        self.protocol._set_valid_events('CIRC')
        self.protocol.add_event_listener(
            'CIRC',
            CallbackChecker(
                "1000 EXTENDED moria1,moria2\nEXTRAMAGIC=99\nANONYMITY=high"
            )
        )
        self.send(b"250 OK")

        d = self.protocol.get_conf("SOCKSPORT ORPORT")
        d.addCallback(CallbackChecker({"ORPORT": "0", "SOCKSPORT": "9050"}))
        self.send(b"650-CIRC 1000 EXTENDED moria1,moria2")
        self.send(b"650-EXTRAMAGIC=99")
        self.send(b"650 ANONYMITY=high")
        self.send(b"250-SOCKSPORT=9050")
        self.send(b"250 ORPORT=0")
        return d

    def test_multiline_plus(self):
        """
        """

        d = self.protocol.get_info("FOO")
        d.addCallback(CallbackChecker({"FOO": "\na\nb\nc"}))
        self.send(b"250+FOO=")
        self.send(b"a")
        self.send(b"b")
        self.send(b"c")
        self.send(b".")
        self.send(b"250 OK")
        return d

    def test_multiline_plus_embedded_equals(self):
        """
        """

        d = self.protocol.get_info("FOO")
        d.addCallback(CallbackChecker({"FOO": "\na="}))
        self.send(b"250+FOO=")
        self.send(b"a=")
        self.send(b".")
        self.send(b"250 OK")
        return d

    def incremental_check(self, expected, actual):
        if '=' in actual:
            return
        self.assertEqual(expected, actual)

    def test_getinfo_incremental(self):
        d = self.protocol.get_info_incremental(
            "FOO",
            functools.partial(self.incremental_check, "bar")
        )
        self.send(b"250+FOO=")
        self.send(b"bar")
        self.send(b"bar")
        self.send(b".")
        self.send(b"250 OK")
        return d

    def test_getinfo_incremental_continuation(self):
        d = self.protocol.get_info_incremental(
            "FOO",
            functools.partial(self.incremental_check, "bar")
        )
        self.send(b"250-FOO=")
        self.send(b"250-bar")
        self.send(b"250-bar")
        self.send(b"250 OK")
        return d

    def test_getinfo_one_line(self):
        d = self.protocol.get_info(
            "foo",
        )
        self.send(b'250 foo=bar')
        d.addCallback(lambda _: functools.partial(self.incremental_check, "bar"))
        return d

    def test_getconf(self):
        d = self.protocol.get_conf("SOCKSPORT ORPORT")
        d.addCallback(CallbackChecker({'SocksPort': '9050', 'ORPort': '0'}))
        self.send(b"250-SocksPort=9050")
        self.send(b"250 ORPort=0")
        return d

    def test_getconf_raw(self):
        d = self.protocol.get_conf_raw("SOCKSPORT ORPORT")
        d.addCallback(CallbackChecker('SocksPort=9050\nORPort=0'))
        self.send(b"250-SocksPort=9050")
        self.send(b"250 ORPort=0")
        return d

    def response_ok(self, v):
        self.assertEqual(v, '')

    def test_setconf(self):
        d = self.protocol.set_conf("foo", "bar").addCallback(
            functools.partial(self.response_ok)
        )
        self.send(b"250 OK")
        self._wait(d)
        self.assertEqual(self.transport.value(), b"SETCONF foo=bar\r\n")

    def test_setconf_with_space(self):
        d = self.protocol.set_conf("foo", "a value with a space")
        d.addCallback(functools.partial(self.response_ok))
        self.send(b"250 OK")
        self._wait(d)
        self.assertEqual(
            self.transport.value(),
            b'SETCONF foo="a value with a space"\r\n'
        )

    def test_setconf_multi(self):
        d = self.protocol.set_conf("foo", "bar", "baz", 1)
        self.send(b"250 OK")
        self._wait(d)
        self.assertEqual(
            self.transport.value(),
            b"SETCONF foo=bar baz=1\r\n",
        )

    def test_quit(self):
        d = self.protocol.quit()
        self.send(b"250 OK")
        self._wait(d)
        self.assertEqual(
            self.transport.value(),
            b"QUIT\r\n",
        )

    def test_dot(self):
        # just checking we don't expode
        self.protocol.graphviz_data()

    def test_debug(self):
        self.protocol.start_debug()
        self.assertTrue(exists('txtorcon-debug.log'))

    def error(self, failure):
        print("ERROR", failure)
        self.assertTrue(False)

    def test_twocommands(self):
        "Two commands on the wire before first response."
        d1 = self.protocol.get_conf("FOO")
        ht = {"a": "one", "b": "two"}
        d1.addCallback(CallbackChecker(ht)).addErrback(log.err)

        d2 = self.protocol.get_info_raw("BAR")
        d2.addCallback(CallbackChecker("bar")).addErrback(log.err)

        self.send(b"250-a=one")
        self.send(b"250-b=two")
        self.send(b"250 OK")
        self.send(b"250 bar")

        return d2

    def test_signal_error(self):
        try:
            self.protocol.signal('FOO')
            self.fail()
        except Exception as e:
            self.assertTrue('Invalid signal' in str(e))

    def test_signal(self):
        self.protocol.valid_signals = ['NEWNYM']
        self.protocol.signal('NEWNYM')
        self.assertEqual(
            self.transport.value(),
            b'SIGNAL NEWNYM\r\n',
        )

    def test_650_after_authenticate(self):
        self.protocol._set_valid_events('CONF_CHANGED')
        self.protocol.add_event_listener(
            'CONF_CHANGED',
            CallbackChecker("Foo=bar")
        )
        self.send(b"250 OK")

        self.send(b"650-CONF_CHANGED")
        self.send(b"650-Foo=bar")

    def test_notify_after_getinfo(self):
        self.protocol._set_valid_events('CIRC')
        self.protocol.add_event_listener(
            'CIRC',
            CallbackChecker("1000 EXTENDED moria1,moria2")
        )
        self.send(b"250 OK")

        d = self.protocol.get_info("a")
        d.addCallback(CallbackChecker({'a': 'one'})).addErrback(self.fail)
        self.send(b"250-a=one")
        self.send(b"250 OK")
        self.send(b"650 CIRC 1000 EXTENDED moria1,moria2")
        return d

    def test_notify_error(self):
        self.protocol._set_valid_events('CIRC')
        self.send(b"650 CIRC 1000 EXTENDED moria1,moria2")

    def test_getinfo(self):
        d = self.protocol.get_info("version")
        d.addCallback(CallbackChecker({'version': '0.2.2.34'}))
        d.addErrback(self.fail)

        self.send(b"250-version=0.2.2.34")
        self.send(b"250 OK")

        self.assertEqual(
            self.transport.value(),
            b"GETINFO version\r\n",
        )
        return d

    def test_getinfo_for_descriptor(self):
        descriptor_info = b"""250+desc/name/moria1=
router moria1 128.31.0.34 9101 0 9131
platform Tor 0.2.5.0-alpha-dev on Linux
protocols Link 1 2 Circuit 1
published 2013-07-05 23:48:52
fingerprint 9695 DFC3 5FFE B861 329B 9F1A B04C 4639 7020 CE31
uptime 1818933
bandwidth 512000 62914560 1307929
extra-info-digest 17D0142F6EBCDF60160EB1794FA6C9717D581F8C
caches-extra-info
onion-key
-----BEGIN RSA PUBLIC KEY-----
MIGJAoGBALzd4bhz1usB7wpoaAvP+BBOnNIk7mByAKV6zvyQ0p1M09oEmxPMc3qD
AAm276oJNf0eq6KWC6YprzPWFsXEIdXSqA6RWXCII1JG/jOoy6nt478BkB8TS9I9
1MJW27ppRaqnLiTmBmM+qzrsgJGwf+onAgUKKH2GxlVgahqz8x6xAgMBAAE=
-----END RSA PUBLIC KEY-----
signing-key
-----BEGIN RSA PUBLIC KEY-----
MIGJAoGBALtJ9uD7cD7iHjqNA3AgsX9prES5QN+yFQyr2uOkxzhvunnaf6SNhzWW
bkfylnMrRm/qCz/czcjZO6N6EKHcXmypehvP566B7gAQ9vDsb+l7VZVWgXvzNc2s
tl3P7qpC08rgyJh1GqmtQTCesIDqkEyWxwToympCt09ZQRq+fIttAgMBAAE=
-----END RSA PUBLIC KEY-----
hidden-service-dir
contact 1024D/28988BF5 arma mit edu
ntor-onion-key 9ZVjNkf/iLEnD685SpC5kcDytQ7u5ViiI9JOftdbE0k=
reject *:*
router-signature
-----BEGIN SIGNATURE-----
Y8Tj2e7mPbFJbguulkPEBVYzyO57p4btpWEXvRMD6vxIh/eyn25pehg5dUVBtZlL
iO3EUE0AEYah2W9gdz8t+i3Dtr0zgqLS841GC/TyDKCm+MKmN8d098qnwK0NGF9q
01NZPuSqXM1b6hnl2espFzL7XL8XEGRU+aeg+f/ukw4=
-----END SIGNATURE-----
.
250 OK"""
        d = self.protocol.get_info("desc/name/moria1")
        d.addCallback(CallbackChecker({'desc/name/moria1': '\n' + '\n'.join(descriptor_info.decode('ascii').split('\n')[1:-2])}))
        d.addErrback(self.fail)

        for line in descriptor_info.split(b'\n'):
            self.send(line)
        return d

    def test_getinfo_multiline(self):
        descriptor_info = b"""250+desc/name/moria1=
router moria1 128.31.0.34 9101 0 9131
platform Tor 0.2.5.0-alpha-dev on Linux
.
250 OK"""
        d = self.protocol.get_info("desc/name/moria1")
        gold = "\nrouter moria1 128.31.0.34 9101 0 9131\nplatform Tor 0.2.5.0-alpha-dev on Linux"
        d.addCallback(CallbackChecker({'desc/name/moria1': gold}))
        d.addErrback(self.fail)

        for line in descriptor_info.split(b'\n'):
            self.send(line)
        return d

    def test_addevent(self):
        self.protocol._set_valid_events('FOO BAR')

        self.protocol.add_event_listener('FOO', lambda _: None)
        # is it dangerous/ill-advised to depend on internal state of
        # class under test?
        d = self.protocol.defer
        self.send(b"250 OK")
        self._wait(d)
        self.assertEqual(
            self.transport.value().split(b'\r\n')[-2],
            b"SETEVENTS FOO"
        )
        self.transport.clear()

        self.protocol.add_event_listener('BAR', lambda _: None)
        d = self.protocol.defer
        self.send(b"250 OK")
        self.assertTrue(
            self.transport.value() == b"SETEVENTS FOO BAR\r\n" or
            self.transport.value() == b"SETEVENTS BAR FOO\r\n"
        )
        self._wait(d)

        try:
            self.protocol.add_event_listener(
                'SOMETHING_INVALID', lambda _: None
            )
            self.assertTrue(False)
        except:
            pass

    def test_eventlistener(self):
        self.protocol._set_valid_events('STREAM')

        class EventListener(object):
            stream_events = 0

            def __call__(self, data):
                self.stream_events += 1

        listener = EventListener()
        self.protocol.add_event_listener('STREAM', listener)

        d = self.protocol.defer
        self.send(b"250 OK")
        self._wait(d)
        self.send(b"650 STREAM 1234 NEW 4321 1.2.3.4:555 REASON=MISC")
        self.send(b"650 STREAM 2345 NEW 4321 2.3.4.5:666 REASON=MISC")
        self.assertEqual(listener.stream_events, 2)

    def test_eventlistener_error(self):
        self.protocol._set_valid_events('STREAM')

        class EventListener(object):
            stream_events = 0
            do_error = False

            def __call__(self, data):
                self.stream_events += 1
                if self.do_error:
                    raise Exception("the bad thing happened")

        # we make sure the first listener has the errors to prove the
        # second one still gets called.
        listener0 = EventListener()
        listener0.do_error = True
        listener1 = EventListener()
        self.protocol.add_event_listener('STREAM', listener0)
        self.protocol.add_event_listener('STREAM', listener1)

        d = self.protocol.defer
        self.send(b"250 OK")
        self._wait(d)
        self.send(b"650 STREAM 1234 NEW 4321 1.2.3.4:555 REASON=MISC")
        self.send(b"650 STREAM 2345 NEW 4321 2.3.4.5:666 REASON=MISC")
        self.assertEqual(listener0.stream_events, 2)
        self.assertEqual(listener1.stream_events, 2)

        # should have logged the two errors
        logged = self.flushLoggedErrors()
        self.assertEqual(2, len(logged))
        self.assertTrue("the bad thing happened" in str(logged[0]))
        self.assertTrue("the bad thing happened" in str(logged[1]))

    def test_remove_eventlistener(self):
        self.protocol._set_valid_events('STREAM')

        class EventListener(object):
            stream_events = 0

            def __call__(self, data):
                self.stream_events += 1

        listener = EventListener()
        self.protocol.add_event_listener('STREAM', listener)
        self.assertEqual(self.transport.value(), b'SETEVENTS STREAM\r\n')
        self.protocol.lineReceived(b"250 OK")
        self.transport.clear()
        self.protocol.remove_event_listener('STREAM', listener)
        self.assertEqual(self.transport.value(), b'SETEVENTS \r\n')

    def test_remove_eventlistener_multiple(self):
        self.protocol._set_valid_events('STREAM')

        class EventListener(object):
            stream_events = 0

            def __call__(self, data):
                self.stream_events += 1

        listener0 = EventListener()
        listener1 = EventListener()
        self.protocol.add_event_listener('STREAM', listener0)
        self.assertEqual(self.transport.value(), b'SETEVENTS STREAM\r\n')
        self.protocol.lineReceived(b"250 OK")
        self.transport.clear()
        # add another one, shouldn't issue a tor command
        self.protocol.add_event_listener('STREAM', listener1)
        self.assertEqual(self.transport.value(), b'')

        # remove one, should still not issue a tor command
        self.protocol.remove_event_listener('STREAM', listener0)
        self.assertEqual(self.transport.value(), b'')

        # remove the other one, NOW should issue a command
        self.protocol.remove_event_listener('STREAM', listener1)
        self.assertEqual(self.transport.value(), b'SETEVENTS \r\n')

        # try removing invalid event
        try:
            self.protocol.remove_event_listener('FOO', listener0)
            self.fail()
        except Exception as e:
            self.assertTrue('FOO' in str(e))

    def test_continuation_line(self):
        d = self.protocol.get_info_raw("key")

        def check_continuation(v):
            self.assertEqual(v, "key=\nvalue0\nvalue1")
        d.addCallback(check_continuation)

        self.send(b"250+key=")
        self.send(b"value0")
        self.send(b"value1")
        self.send(b".")
        self.send(b"250 OK")

        return d

    def test_newdesc(self):
        """
        FIXME: this test is now maybe a little silly, it's just testing
        multiline GETINFO...  (Real test is in
        TorStateTests.test_newdesc_parse)
        """

        self.protocol.get_info_raw('ns/id/624926802351575FF7E4E3D60EFA3BFB56E67E8A')
        d = self.protocol.defer
        d.addCallback(CallbackChecker("""ns/id/624926802351575FF7E4E3D60EFA3BFB56E67E8A=
r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid
w Bandwidth=518000
p accept 43,53,79-81,110,143,194,220,443,953,989-990,993,995,1194,1293,1723,1863,2082-2083,2086-2087,2095-2096,3128,4321,5050,5190,5222-5223,6679,6697,7771,8000,8008,8080-8081,8090,8118,8123,8181,8300,8443,8888"""))

        self.send(b"250+ns/id/624926802351575FF7E4E3D60EFA3BFB56E67E8A=")
        self.send(b"r fake YkkmgCNRV1/35OPWDvo7+1bmfoo tanLV/4ZfzpYQW0xtGFqAa46foo 2011-12-12 16:29:16 12.45.56.78 443 80")
        self.send(b"s Exit Fast Guard HSDir Named Running Stable V2Dir Valid")
        self.send(b"w Bandwidth=518000")
        self.send(b"p accept 43,53,79-81,110,143,194,220,443,953,989-990,993,995,1194,1293,1723,1863,2082-2083,2086-2087,2095-2096,3128,4321,5050,5190,5222-5223,6679,6697,7771,8000,8008,8080-8081,8090,8118,8123,8181,8300,8443,8888")
        self.send(b".")
        self.send(b"250 OK")

        return d

    def test_plus_line_no_command(self):
        self.protocol.lineReceived(b"650+NS\r\n")
        self.protocol.lineReceived(b"r Gabor gFpAHsFOHGATy12ZUswRf0ZrqAU GG6GDp40cQfR3ODvkBT0r+Q09kw 2012-05-12 16:54:56 91.219.238.71 443 80\r\n")

    def test_minus_line_no_command(self):
        """
        haven't seen 600's use - "in the wild" but don't see why it's not
        possible
        """
        self.protocol._set_valid_events('NS')
        self.protocol.add_event_listener('NS', lambda _: None)
        self.protocol.lineReceived(b"650-NS\r\n")
        self.protocol.lineReceived(b"650 OK\r\n")


class ParseTests(unittest.TestCase):

    def setUp(self):
        self.controller = TorState(TorControlProtocol())
        self.controller.connectionMade = lambda _: None

    def test_keywords(self):
        x = parse_keywords('events/names=CIRC STREAM ORCONN BW DEBUG INFO NOTICE WARN ERR NEWDESC ADDRMAP AUTHDIR_NEWDESCS DESCCHANGED NS STATUS_GENERAL STATUS_CLIENT STATUS_SERVER GUARD STREAM_BW CLIENTS_SEEN NEWCONSENSUS BUILDTIMEOUT_SET')
        self.assertTrue('events/names' in x)
        self.assertEqual(x['events/names'], 'CIRC STREAM ORCONN BW DEBUG INFO NOTICE WARN ERR NEWDESC ADDRMAP AUTHDIR_NEWDESCS DESCCHANGED NS STATUS_GENERAL STATUS_CLIENT STATUS_SERVER GUARD STREAM_BW CLIENTS_SEEN NEWCONSENSUS BUILDTIMEOUT_SET')
        self.assertEqual(len(x.keys()), 1)

    def test_keywords_mutli_equals(self):
        x = parse_keywords('foo=something subvalue="foo"')
        self.assertEqual(len(x), 1)
        self.assertTrue('foo' in x)
        self.assertEqual(x['foo'], 'something subvalue="foo"')

    def test_default_keywords(self):
        x = parse_keywords('foo')
        self.assertEqual(len(x), 1)
        self.assertTrue('foo' in x)
        self.assertEqual(x['foo'], DEFAULT_VALUE)

    def test_multientry_keywords_2(self):
        x = parse_keywords('foo=bar\nfoo=zarimba')
        self.assertEqual(len(x), 1)
        self.assertTrue(isinstance(x['foo'], list))
        self.assertEqual(len(x['foo']), 2)
        self.assertEqual(x['foo'][0], 'bar')
        self.assertEqual(x['foo'][1], 'zarimba')

    def test_multientry_keywords_3(self):
        x = parse_keywords('foo=bar\nfoo=baz\nfoo=zarimba')
        self.assertEqual(len(x), 1)
        self.assertTrue(isinstance(x['foo'], list))
        self.assertEqual(len(x['foo']), 3)
        self.assertEqual(x['foo'][0], 'bar')
        self.assertEqual(x['foo'][1], 'baz')
        self.assertEqual(x['foo'][2], 'zarimba')

    def test_multientry_keywords_4(self):
        x = parse_keywords('foo=bar\nfoo=baz\nfoo=zarimba\nfoo=foo')
        self.assertEqual(len(x), 1)
        self.assertTrue(isinstance(x['foo'], list))
        self.assertEqual(len(x['foo']), 4)
        self.assertEqual(x['foo'][0], 'bar')
        self.assertEqual(x['foo'][1], 'baz')
        self.assertEqual(x['foo'][2], 'zarimba')
        self.assertEqual(x['foo'][3], 'foo')

    def test_multiline_keywords_with_spaces(self):
        x = parse_keywords('''ns/name/foo=
r foo aaaam7E7h1vY5Prk8v9/nSRCydY BBBBOfum4CtAYuOgf/D33Qq5+rk 2013-10-27 06:22:18 1.2.3.4 9001 9030
s Fast Guard HSDir Running Stable V2Dir Valid
w Bandwidth=1234
ns/name/bar=
r bar aaaaHgNYtTVPw5hHTO28J4je5i8 BBBBBUaJaBFSU/HDrTxnSh+D3+fY 2013-10-27 07:48:56 1.2.4.5 9001 9030
s Exit Fast Guard HSDir Named Running Stable V2Dir Valid
w Bandwidth=1234
OK
''')
        self.assertEqual(2, len(x))
        keys = sorted(x.keys())
        self.assertEqual(keys, ['ns/name/bar', 'ns/name/foo'])

    def test_multiline_keywords(self):
        x = parse_keywords('''Foo=bar\nBar''')
        self.assertEqual(x, {'Foo': 'bar\nBar'})
        x = parse_keywords('''Foo=bar\nBar''', multiline_values=False)
        self.assertEqual(x, {'Foo': 'bar',
                             'Bar': DEFAULT_VALUE})

    def test_unquoted_keywords(self):
        x = parse_keywords('''Tor="0.1.2.3.4-rc44"''')
        self.assertEqual(x, {'Tor': '0.1.2.3.4-rc44'})

    def test_unquoted_keywords_singlequote(self):
        x = parse_keywords("Tor='0.1.2.3.4-rc44'")
        self.assertEqual(x, {'Tor': '0.1.2.3.4-rc44'})

    def test_unquoted_keywords_empty(self):
        x = parse_keywords('foo=')
        self.assertEqual(x, {'foo': ''})

    def test_network_status(self):
        self.controller._update_network_status("""ns/all=
r right2privassy3 ADQ6gCT3DiFHKPDFr3rODBUI8HM JehnjB8l4Js47dyjLCEmE8VJqao 2011-12-02 03:36:40 50.63.8.215 9023 0
s Exit Fast Named Running Stable Valid
w Bandwidth=53
p accept 80,1194,1220,1293,1500,1533,1677,1723,1863,2082-2083,2086-2087,2095-2096,2102-2104,3128,3389,3690,4321,4643,5050,5190,5222-5223,5228,5900,6660-6669,6679,6697,8000,8008,8074,8080,8087-8088,8443,8888,9418,9999-10000,19294,19638
r Unnamed AHe2V2pmj4Yfn0H9+Np3lci7htU T/g7ZLzG/ooqCn+gdLd9Jjh+AEI 2011-12-02 15:52:09 84.101.216.232 443 9030
s Exit Fast Running V2Dir Valid
w Bandwidth=33
p reject 25,119,135-139,445,563,1214,4661-4666,6346-6429,6699,6881-6999""")
        # the routers list is always keyed with both name and hash
        self.assertEqual(len(self.controller.routers_by_name), 2)
        self.assertEqual(len(self.controller.routers_by_hash), 2)
        self.assertTrue('right2privassy3' in self.controller.routers)
        self.assertTrue('Unnamed' in self.controller.routers)

        self.controller.routers.clear()
        self.controller.routers_by_name.clear()
        self.controller.routers_by_hash.clear()

    def test_circuit_status(self):
        self.controller._update_network_status("""ns/all=
r wildnl f+Ty/+B6lgYr0Ntbf67O/L2M8ZI c1iK/kPPXKGZZvwXRWbvL9eCfSc 2011-12-02 19:07:05 209.159.142.164 9001 0
s Exit Fast Named Running Stable Valid
w Bandwidth=1900
p reject 25,119,135-139,445,563,1214,4661-4666,6346-6429,6699,6881-6999
r l0l wYXUpLBpzVWfzVSMgGO0dThdd38 KIJC+W1SHeaFOj/BVsEAgxbtQNM 2011-12-02 13:43:39 94.23.168.39 443 80
s Fast Named Running Stable V2Dir Valid
w Bandwidth=22800
p reject 1-65535
r Tecumseh /xAD0tFLS50Dkz+O37xGyVLoKlk yJHbad7MFl1VW2/23RxrPKBTOIE 2011-12-02 09:44:10 76.73.48.211 22 9030
s Fast Guard HSDir Named Running Stable V2Dir Valid
w Bandwidth=18700
p reject 1-65535""")
        self.controller._circuit_status("""circuit-status=
4472 BUILT $FF1003D2D14B4B9D03933F8EDFBC46C952E82A59=Tecumseh,$C185D4A4B069CD559FCD548C8063B475385D777F=l0l,$7FE4F2FFE07A96062BD0DB5B7FAECEFCBD8CF192=wildnl PURPOSE=GENERAL""")
        self.assertEqual(len(self.controller.circuits), 1)
        self.assertTrue(4472 in self.controller.circuits)

        self.controller.routers.clear()
        self.controller.routers_by_name.clear()
        self.controller.routers_by_hash.clear()
        self.controller.circuits.clear()
