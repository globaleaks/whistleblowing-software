import os
import sys
import tempfile
from mock import patch
from unittest import skipIf
import ipaddress

from twisted.trial import unittest
from twisted.internet import defer
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.interfaces import IProtocolFactory
from zope.interface import implementer

from txtorcon.util import process_from_address
from txtorcon.util import delete_file_or_tree
from txtorcon.util import find_keywords
from txtorcon.util import ip_from_int
from txtorcon.util import find_tor_binary
from txtorcon.util import maybe_ip_addr
from txtorcon.util import unescape_quoted_string
from txtorcon.util import available_tcp_port
from txtorcon.util import version_at_least
from txtorcon.util import default_control_port
from txtorcon.util import _Listener, _ListenerCollection
from txtorcon.util import create_tbb_web_headers


class FakeState:
    tor_pid = 0


@implementer(IProtocolFactory)
class FakeProtocolFactory:

    def doStart(self):
        "IProtocolFactory API"

    def doStop(self):
        "IProtocolFactory API"

    def buildProtocol(self, addr):
        "IProtocolFactory API"
        return None


class TestIPFromInt(unittest.TestCase):

    def test_cast(self):
        self.assertEqual(ip_from_int(0x7f000001), '127.0.0.1')


class TestGeoIpDatabaseLoading(unittest.TestCase):

    def test_bad_geoip_path(self):
        "fail gracefully if a db is missing"
        from txtorcon import util
        self.assertRaises(IOError, util.create_geoip, '_missing_path_')

    def test_missing_geoip_module(self):
        "return none if geoip module is missing"
        from txtorcon import util
        _GeoIP = util.GeoIP
        util.GeoIP = None
        (fd, f) = tempfile.mkstemp()
        ret_val = util.create_geoip(f)
        delete_file_or_tree(f)
        util.GeoIP = _GeoIP
        self.assertEqual(ret_val, None)

    @skipIf('pypy' in sys.version.lower(), "No GeoIP in PyPy")
    def test_return_geoip_object(self):
        from txtorcon import util
        (fd, f) = tempfile.mkstemp()
        ret_val = util.create_geoip(f)
        delete_file_or_tree(f)
        self.assertEqual(type(ret_val).__name__, 'GeoIP')


class TestFindKeywords(unittest.TestCase):

    def test_filter(self):
        "make sure we filter out keys that look like router IDs"
        self.assertEqual(
            find_keywords("foo=bar $1234567890=routername baz=quux".split()),
            {'foo': 'bar', 'baz': 'quux'}
        )


class FakeGeoIP(object):
    def __init__(self, version=2):
        self.version = version

    def record_by_addr(self, ip):
        r = dict(country_code='XX',
                 latitude=50.0,
                 longitude=0.0,
                 city='City')
        if self.version == 2:
            r['region_code'] = 'Region'
        else:
            r['region_name'] = 'Region'
        return r


class TestNetLocation(unittest.TestCase):

    def test_valid_lookup_v2(self):
        from txtorcon import util
        orig = util.city
        try:
            util.city = FakeGeoIP(version=2)
            nl = util.NetLocation('127.0.0.1')
            self.assertTrue(nl.city)
            self.assertEqual(nl.city[0], 'City')
            self.assertEqual(nl.city[1], 'Region')
        finally:
            util.ity = orig

    def test_valid_lookup_v3(self):
        from txtorcon import util
        orig = util.city
        try:
            util.city = FakeGeoIP(version=3)
            nl = util.NetLocation('127.0.0.1')
            self.assertTrue(nl.city)
            self.assertEqual(nl.city[0], 'City')
            self.assertEqual(nl.city[1], 'Region')
        finally:
            util.ity = orig

    def test_city_fails(self):
        "make sure we don't fail if the city lookup excepts"
        from txtorcon import util
        orig = util.city
        try:
            class Thrower(object):
                def record_by_addr(*args, **kw):
                    raise RuntimeError("testing failure")
            util.city = Thrower()
            nl = util.NetLocation('127.0.0.1')
            self.assertEqual(None, nl.city)

        finally:
            util.city = orig

    def test_no_city_db(self):
        "ensure we lookup from country if we have no city"
        from txtorcon import util
        origcity = util.city
        origcountry = util.country
        try:
            util.city = None
            obj = object()

            class CountryCoder(object):
                def country_code_by_addr(self, ipaddr):
                    return obj
            util.country = CountryCoder()
            nl = util.NetLocation('127.0.0.1')
            self.assertEqual(obj, nl.countrycode)

        finally:
            util.city = origcity
            util.country = origcountry

    def test_no_city_or_country_db(self):
        "ensure we lookup from asn if we have no city or country"
        from txtorcon import util
        origcity = util.city
        origcountry = util.country
        origasn = util.asn
        try:
            util.city = None
            util.country = None

            class Thrower:
                def org_by_addr(*args, **kw):
                    raise RuntimeError("testing failure")
            util.asn = Thrower()
            nl = util.NetLocation('127.0.0.1')
            self.assertEqual('', nl.countrycode)

        finally:
            util.city = origcity
            util.country = origcountry
            util.asn = origasn


class TestProcessFromUtil(unittest.TestCase):

    def setUp(self):
        self.fakestate = FakeState()

    def test_none(self):
        "ensure we do something useful on a None address"
        self.assertEqual(process_from_address(None, 80, self.fakestate), None)

    def test_internal(self):
        "look up the (Tor_internal) PID"
        pfa = process_from_address('(Tor_internal)', 80, self.fakestate)
        # depends on whether you have psutil installed or not, and on
        # whether your system always has a PID 0 process...
        self.assertEqual(pfa, self.fakestate.tor_pid)

    def test_internal_no_state(self):
        "look up the (Tor_internal) PID"
        pfa = process_from_address('(Tor_internal)', 80)
        # depends on whether you have psutil installed or not, and on
        # whether your system always has a PID 0 process...
        self.assertEqual(pfa, None)

    @defer.inlineCallbacks
    def test_real_addr(self):
        # FIXME should choose a port which definitely isn't used.

        # it's apparently frowned upon to use the "real" reactor in
        # tests, but I was using "nc" before, and I think this is
        # preferable.
        from twisted.internet import reactor
        port = yield available_tcp_port(reactor)
        ep = TCP4ServerEndpoint(reactor, port)
        listener = yield ep.listen(FakeProtocolFactory())

        try:
            pid = process_from_address('0.0.0.0', port, self.fakestate)
        finally:
            listener.stopListening()

        self.assertEqual(pid, os.getpid())


class TestDelete(unittest.TestCase):

    def test_delete_file(self):
        (fd, f) = tempfile.mkstemp()
        os.write(fd, b'some\ndata\n')
        os.close(fd)
        self.assertTrue(os.path.exists(f))
        delete_file_or_tree(f)
        self.assertTrue(not os.path.exists(f))

    def test_delete_tree(self):
        d = tempfile.mkdtemp()
        f = open(os.path.join(d, 'foo'), 'wb')
        f.write(b'foo\n')
        f.close()

        self.assertTrue(os.path.exists(d))
        self.assertTrue(os.path.isdir(d))
        self.assertTrue(os.path.exists(os.path.join(d, 'foo')))

        delete_file_or_tree(d)

        self.assertTrue(not os.path.exists(d))
        self.assertTrue(not os.path.exists(os.path.join(d, 'foo')))


class TestFindTor(unittest.TestCase):

    def test_simple_find_tor(self):
        # just test that this doesn't raise an exception
        find_tor_binary()

    def test_find_tor_globs(self):
        "test searching by globs"
        find_tor_binary(system_tor=False)

    def test_find_tor_unfound(self):
        "test searching by globs"
        self.assertEqual(None, find_tor_binary(system_tor=False, globs=()))

    @patch('txtorcon.util.subprocess.Popen')
    def test_find_ioerror(self, popen):
        "test searching with which, but it fails"
        popen.side_effect = OSError
        self.assertEqual(None, find_tor_binary(system_tor=True, globs=()))


class TestIpAddr(unittest.TestCase):

    def test_create_ipaddr(self):
        ip = maybe_ip_addr('1.2.3.4')
        self.assertTrue(isinstance(ip, ipaddress.IPv4Address))

    @patch('txtorcon.util.ipaddress')
    def test_create_ipaddr_fail(self, ipaddr):
        def foo(blam):
            raise ValueError('testing')
        ipaddr.ip_address.side_effect = foo
        ip = maybe_ip_addr('1.2.3.4')
        self.assertTrue(isinstance(ip, type('1.2.3.4')))


class TestUnescapeQuotedString(unittest.TestCase):
    '''
    Test cases for the function unescape_quoted_string.
    '''
    def test_valid_string_unescaping(self):
        unescapeable = {
            '\\\\': '\\',         # \\     -> \
            r'\"': r'"',          # \"     -> "
            r'\\\"': r'\"',       # \\\"   -> \"
            r'\\\\\"': r'\\"',    # \\\\\" -> \\"
            '\\"\\\\': '"\\',     # \"\\   -> "\
            "\\'": "'",           # \'     -> '
            "\\\\\\'": "\\'",     # \\\'   -> \
            r'some\"text': 'some"text',
            'some\\word': 'someword',
            '\\delete\\ al\\l un\\used \\backslashes': 'delete all unused backslashes',
            '\\n\\r\\t': '\n\r\t',
            '\\x00 \\x0123': 'x00 x0123',
            '\\\\x00 \\\\x00': '\\x00 \\x00',
            '\\\\\\x00  \\\\\\x00': '\\x00  \\x00'
        }

        for escaped, correct_unescaped in unescapeable.items():
            escaped = '"{}"'.format(escaped)
            unescaped = unescape_quoted_string(escaped)
            msg = "Wrong unescape: {escaped} -> {unescaped} instead of {correct}"
            msg = msg.format(unescaped=unescaped, escaped=escaped,
                             correct=correct_unescaped)
            self.assertEqual(unescaped, correct_unescaped, msg=msg)

    def test_string_unescape_octals(self):
        '''
        Octal numbers can be escaped by a backslash:
        \0 is interpreted as a byte with the value 0
        '''
        for number in range(0x7f):
            escaped = '\\%o' % number
            result = unescape_quoted_string('"{}"'.format(escaped))
            expected = chr(number)

            msg = "Number not decoded correctly: {escaped} -> {result} instead of {expected}"
            msg = msg.format(escaped=escaped, result=repr(result), expected=repr(expected))
            self.assertEqual(result, expected, msg=msg)

    def test_invalid_string_unescaping(self):
        invalid_escaped = [
            '"""',       # "     - unescaped quote
            '"\\"',      # \     - unescaped backslash
            '"\\\\\\"',  # \\\   - uneven backslashes
            '"\\\\""',   # \\"   - quotes not escaped
        ]

        for invalid_string in invalid_escaped:
            self.assertRaises(ValueError, unescape_quoted_string, invalid_string)


class TestVersions(unittest.TestCase):
    def test_version_1(self):
        self.assertTrue(
            version_at_least("1.2.3.4", 1, 2, 3, 4)
        )

    def test_version_2(self):
        self.assertFalse(
            version_at_least("1.2.3.4", 1, 2, 3, 5)
        )

    def test_version_3(self):
        self.assertTrue(
            version_at_least("1.2.3.4", 1, 2, 3, 2)
        )

    def test_version_4(self):
        self.assertTrue(
            version_at_least("2.1.1.1", 2, 0, 0, 0)
        )


class TestHeaders(unittest.TestCase):

    def test_simple(self):
        create_tbb_web_headers()


class TestDefaultPort(unittest.TestCase):

    def test_no_env_var(self):
        p = default_control_port()
        self.assertEqual(p, 9151)

    @patch('txtorcon.util.os')
    def test_env_var(self, fake_os):
        fake_os.environ = dict(TX_CONTROL_PORT=1234)
        p = default_control_port()
        self.assertEqual(p, 1234)


class TestListeners(unittest.TestCase):

    def test_add_remove(self):
        listener = _Listener()
        calls = []

        def cb(*args, **kw):
            calls.append((args, kw))

        listener.add(cb)
        listener.notify('foo', 'bar', quux='zing')
        listener.remove(cb)
        listener.notify('foo', 'bar', quux='zing')

        self.assertEqual(1, len(calls))
        self.assertEqual(('foo', 'bar'), calls[0][0])
        self.assertEqual(dict(quux='zing'), calls[0][1])

    def test_notify_with_exception(self):
        listener = _Listener()
        calls = []

        def cb(*args, **kw):
            calls.append((args, kw))

        def bad_cb(*args, **kw):
            raise Exception("sadness")

        listener.add(bad_cb)
        listener.add(cb)
        listener.notify('foo', 'bar', quux='zing')

        self.assertEqual(1, len(calls))
        self.assertEqual(('foo', 'bar'), calls[0][0])
        self.assertEqual(dict(quux='zing'), calls[0][1])

    def test_collection_invalid_event(self):
        collection = _ListenerCollection(['event0', 'event1'])

        with self.assertRaises(Exception) as ctx:
            collection('bad', lambda: None)
        self.assertTrue('Invalid event' in str(ctx.exception))

    def test_collection_invalid_event_notify(self):
        collection = _ListenerCollection(['event0', 'event1'])

        with self.assertRaises(Exception) as ctx:
            collection.notify('bad', lambda: None)
        self.assertTrue('Invalid event' in str(ctx.exception))

    def test_collection_invalid_event_remove(self):
        collection = _ListenerCollection(['event0', 'event1'])

        with self.assertRaises(Exception) as ctx:
            collection.remove('bad', lambda: None)
        self.assertTrue('Invalid event' in str(ctx.exception))

    def test_collection(self):
        collection = _ListenerCollection(['event0', 'event1'])
        calls = []

        def cb(*args, **kw):
            calls.append((args, kw))

        collection('event0', cb)
        collection.notify('event0', 'foo', 'bar', quux='zing')
        collection.remove('event0', cb)
        collection.notify('event0', 'foo', 'bar', quux='zing')

        self.assertEqual(1, len(calls))
        self.assertEqual(calls[0][0], ('foo', 'bar'))
        self.assertEqual(calls[0][1], dict(quux='zing'))
