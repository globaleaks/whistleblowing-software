# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import glob
import os
import hmac
import hashlib
import shutil
import socket
import subprocess
import ipaddress
import struct
import re
import six

from twisted.internet import defer
from twisted.internet.interfaces import IProtocolFactory
from twisted.internet.endpoints import serverFromString
from twisted.web.http_headers import Headers

from zope.interface import implementer
from zope.interface import Interface

if six.PY3:
    import asyncio

try:
    import GeoIP as _GeoIP
    GeoIP = _GeoIP
except ImportError:
    GeoIP = None

city = None
country = None
asn = None


def create_tbb_web_headers():
    """
    Returns a new `twisted.web.http_headers.Headers` instance
    populated with tags to mimic Tor Browser. These include values for
    `User-Agent`, `Accept`, `Accept-Language` and `Accept-Encoding`.
    """
    return Headers({
        b"User-Agent": [b"Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0"],
        b"Accept": [b"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"],
        b"Accept-Language": [b"en-US,en;q=0.5"],
        b"Accept-Encoding": [b"gzip, deflate"],
    })


def version_at_least(version_string, major, minor, micro, patch):
    """
    This returns True if the version_string represents a Tor version
    of at least ``major``.``minor``.``micro``.``patch`` version,
    ignoring any trailing specifiers.
    """
    parts = re.match(
        r'^([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+).*$',
        version_string,
    )
    for ver, gold in zip(parts.group(1, 2, 3, 4), (major, minor, micro, patch)):
        if int(ver) < int(gold):
            return False
        elif int(ver) > int(gold):
            return True
    return True


def create_geoip(fname):
    # It's more "pythonic" to just wait for the exception,
    # but GeoIP prints out "Can't open..." messages for you,
    # which isn't desired here
    if not os.path.isfile(fname):
        raise IOError("Can't find %s" % fname)

    if GeoIP is None:
        return None

    # just letting any errors make it out
    return GeoIP.open(fname, GeoIP.GEOIP_STANDARD)


def maybe_create_db(path):
    try:
        return create_geoip(path)
    except IOError:
        return None


city = maybe_create_db("/usr/share/GeoIP/GeoLiteCity.dat")
asn = maybe_create_db("/usr/share/GeoIP/GeoIPASNum.dat")
country = maybe_create_db("/usr/share/GeoIP/GeoIP.dat")


def is_executable(path):
    """Checks if the given path points to an existing, executable file"""
    return os.path.isfile(path) and os.access(path, os.X_OK)


def find_tor_binary(globs=('/usr/sbin/', '/usr/bin/',
                           '/Applications/TorBrowser_*.app/Contents/MacOS/'),
                    system_tor=True):
    """
    Tries to find the tor executable using the shell first or in in the
    paths whose glob-patterns is in the given 'globs'-tuple.

    :param globs:
        A tuple of shell-style globs of directories to use to find tor
        (TODO consider making that globs to actual tor binary?)

    :param system_tor:
        This controls whether bash is used to seach for 'tor' or
        not. If False, we skip that check and use only the 'globs'
        tuple.
    """

    # Try to find the tor executable using the shell
    if system_tor:
        try:
            proc = subprocess.Popen(
                ('which tor'),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True
            )
        except OSError:
            pass
        else:
            stdout, _ = proc.communicate()
            if proc.poll() == 0 and stdout != '':
                return stdout.strip()

    # the shell may not provide type and tor is usually not on PATH when using
    # the browser-bundle. Look in specific places
    for pattern in globs:
        for path in glob.glob(pattern):
            torbin = os.path.join(path, 'tor')
            if is_executable(torbin):
                return torbin
    return None


def maybe_ip_addr(addr):
    """
    Tries to return an IPAddress, otherwise returns a string.

    TODO consider explicitly checking for .exit or .onion at the end?
    """

    if six.PY2 and isinstance(addr, str):
        addr = unicode(addr)  # noqa
    try:
        return ipaddress.ip_address(addr)
    except ValueError:
        pass
    return str(addr)


def find_keywords(args, key_filter=lambda x: not x.startswith("$")):
    """
    This splits up strings like name=value, foo=bar into a dict. Does NOT deal
    with quotes in value (e.g. key="value with space" will not work

    By default, note that it takes OUT any key which starts with $ (i.e. a
    single dollar sign) since for many use-cases the way Tor encodes nodes
    with "$hash=name" looks like a keyword argument (but it isn't). If you
    don't want this, override the "key_filter" argument to this method.

    :param args: a list of strings, each with one key=value pair

    :return:
        a dict of key->value (both strings) of all name=value type
        keywords found in args.
    """
    filtered = [x for x in args if '=' in x and key_filter(x.split('=')[0])]
    return dict(x.split('=', 1) for x in filtered)


def delete_file_or_tree(*args):
    """
    For every path in args, try to delete it as a file or a directory
    tree. Ignores deletion errors.
    """

    for f in args:
        try:
            os.unlink(f)
        except OSError:
            shutil.rmtree(f, ignore_errors=True)


def ip_from_int(ip):
        """ Convert long int back to dotted quad string """
        return socket.inet_ntoa(struct.pack('>I', ip))


def process_from_address(addr, port, torstate=None):
    """
    Determines the PID from the address/port provided by using lsof
    and returns it as an int (or None if it couldn't be
    determined). In the special case the addr is '(Tor_internal)' then
    the PID of the Tor process (as gotten from the torstate object) is
    returned (or 0 if unavailable, e.g. a Tor which doesn't implement
    'GETINFO process/pid'). In this case if no TorState instance is
    given, None is returned.
    """

    if addr is None:
        return None

    if "(tor_internal)" == str(addr).lower():
        if torstate is None:
            return None
        return int(torstate.tor_pid)

    proc = subprocess.Popen(['lsof', '-i', '4tcp@%s:%s' % (addr, port)],
                            stdout=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    lines = stdout.split(b'\n')
    if len(lines) > 1:
        return int(lines[1].split()[1])


def hmac_sha256(key, msg):
    """
    Adapted from rransom's tor-utils git repository. Returns the
    digest (binary) of an HMAC with SHA256 over msg with key.
    """

    return hmac.new(key, msg, hashlib.sha256).digest()


CRYPTOVARIABLE_EQUALITY_COMPARISON_NONCE = os.urandom(32)


def compare_via_hash(x, y):
    """
    Taken from rransom's tor-utils git repository, to compare two
    hashes in something resembling constant time (or at least, not
    leaking timing info?)
    """
    return (hmac_sha256(CRYPTOVARIABLE_EQUALITY_COMPARISON_NONCE, x) ==
            hmac_sha256(CRYPTOVARIABLE_EQUALITY_COMPARISON_NONCE, y))


class NetLocation(object):
    """
    Represents the location of an IP address, either city or country
    level resolution depending on what GeoIP database was loaded. If
    the ASN database is available you get that also.
    """

    def __init__(self, ipaddr):
        "ipaddr should be a dotted-quad"
        self.ip = ipaddr
        self.latlng = (None, None)
        self.countrycode = None
        self.city = None
        self.asn = None

        if self.ip is None or self.ip == 'unknown':
            return

        if city:
            try:
                r = city.record_by_addr(self.ip)
            except Exception:
                r = None
            if r is not None:
                self.countrycode = r['country_code']
                self.latlng = (r['latitude'], r['longitude'])
                try:
                    self.city = (r['city'], r['region_code'])
                except KeyError:
                    self.city = (r['city'], r['region_name'])

        elif country:
            self.countrycode = country.country_code_by_addr(ipaddr)

        else:
            self.countrycode = ''

        if asn:
            try:
                self.asn = asn.org_by_addr(self.ip)
            except Exception:
                self.asn = None


@implementer(IProtocolFactory)
class NoOpProtocolFactory:
    """
    This is an IProtocolFactory that does nothing. Used for testing,
    and for :method:`available_tcp_port`
    """
    def noop(self, *args, **kw):
        pass
    buildProtocol = noop
    doStart = noop
    doStop = noop


@defer.inlineCallbacks
def available_tcp_port(reactor):
    """
    Returns a Deferred firing an available TCP port on localhost.
    It does so by listening on port 0; then stopListening and fires the
    assigned port number.
    """

    endpoint = serverFromString(reactor, 'tcp:0:interface=127.0.0.1')
    port = yield endpoint.listen(NoOpProtocolFactory())
    address = port.getHost()
    yield port.stopListening()
    defer.returnValue(address.port)


def unescape_quoted_string(string):
    r'''
    This function implementes the recommended functionality described in the
    tor control-spec to be compatible with older tor versions:

      * Read \\n \\t \\r and \\0 ... \\377 as C escapes.
      * Treat a backslash followed by any other character as that character.

    Except the legacy support for the escape sequences above this function
    implements parsing of QuotedString using qcontent from

    QuotedString = DQUOTE *qcontent DQUOTE

    :param string: The escaped quoted string.
    :returns: The unescaped string.
    :raises ValueError: If the string is in a invalid form
                        (e.g. a single backslash)
    '''
    match = re.match(r'''^"((?:[^"\\]|\\.)*)"$''', string)
    if not match:
        raise ValueError("Invalid quoted string", string)
    string = match.group(1)
    # remove backslash before all characters which should not be
    # handeled as escape codes by string.decode('string-escape').
    # This is needed so e.g. '\x00' is not unescaped as '\0'
    string = re.sub(r'((?:^|[^\\])(?:\\\\)*)\\([^ntr0-7\\])', r'\1\2', string)
    if six.PY3:
        # XXX hmmm?
        return bytes(string, 'ascii').decode('unicode-escape')
    return string.decode('string-escape')


def default_control_port():
    """
    This returns a default control port, which respects an environment
    variable `TX_CONTROL_PORT`. Without the environment variable, this
    returns 9151 (the Tor Browser Bundle default).

    You shouldn't use this in "normal" code, this is a convenience for
    the examples.
    """
    try:
        return int(os.environ['TX_CONTROL_PORT'])
    except KeyError:
        return 9151


class IListener(Interface):
    def add(callback):
        """
        Add a listener. The arguments to the callback are determined by whomever calls notify()
        """

    def remove(callback):
        """
        Add a listener. The arguments to the callback are determined by whomever calls notify()
        """

    def notify(*args, **kw):
        """
        Calls every listener with the given args and keyword-args.

        XXX errors? just log?
        """


def maybe_coroutine(obj):
    """
    If 'obj' is a coroutine and we're using Python3, wrap it in
    ensureDeferred. Otherwise return the original object.

    (This is to insert in all callback chains from user code, in case
    that user code is Python3 and used 'async def')
    """
    if six.PY3 and asyncio.iscoroutine(obj):
        return defer.ensureDeferred(obj)
    return obj


@implementer(IListener)
class _Listener(object):
    """
    Internal helper.
    """

    def __init__(self):
        self._listeners = set()

    def add(self, callback):
        """
        Add a callback to this listener
        """
        self._listeners.add(callback)

    __call__ = add  #: alias for "add"

    def remove(self, callback):
        """
        Remove a callback from this listener
        """
        self._listeners.remove(callback)

    def notify(self, *args, **kw):
        """
        Calls all listeners with the specified args.

        Returns a Deferred which callbacks when all the listeners
        which return Deferreds have themselves completed.
        """
        calls = []

        def failed(fail):
            # XXX use logger
            fail.printTraceback()

        for cb in self._listeners:
            d = defer.maybeDeferred(cb, *args, **kw)
            d.addCallback(maybe_coroutine)
            d.addErrback(failed)
            calls.append(d)
        return defer.DeferredList(calls)


class _ListenerCollection(object):
    """
    Internal helper.

    This collects all your valid event listeners together in one
    object if you want.
    """
    def __init__(self, valid_events):
        self._valid_events = valid_events
        for e in valid_events:
            setattr(self, e, _Listener())

    def __call__(self, event, callback):
        if event not in self._valid_events:
            raise Exception("Invalid event '{}'".format(event))
        getattr(self, event).add(callback)

    def remove(self, event, callback):
        if event not in self._valid_events:
            raise Exception("Invalid event '{}'".format(event))
        getattr(self, event).remove(callback)

    def notify(self, event, *args, **kw):
        if event not in self._valid_events:
            raise Exception("Invalid event '{}'".format(event))
        getattr(self, event).notify(*args, **kw)


# similar to OneShotObserverList in Tahoe-LAFS
class SingleObserver(object):
    """
    A helper for ".when_*()" sort of functions.
    """
    _NotFired = object()

    def __init__(self):
        self._observers = []
        self._fired = self._NotFired

    def when_fired(self):
        d = defer.Deferred()
        if self._fired is not self._NotFired:
            d.callback(self._fired)
        else:
            self._observers.append(d)
        return d

    def fire(self, value):
        if self._observers is None:
            return  # raise RuntimeError("already fired") ?
        self._fired = value
        for d in self._observers:
            d.callback(self._fired)
        self._observers = None
        return value  # so we're transparent if used as a callback


class _Version(object):
    """
    Replacement for incremental.Version until
    https://github.com/meejah/txtorcon/issues/233 and/or
    https://github.com/hawkowl/incremental/issues/31 is fixed.
    """
    # as of latest incremental, it should only access .package and
    # .short() via the getVersionString() method that Twisted's
    # deprecated() uses...

    def __init__(self, package, major, minor, patch):
        self.package = package
        self.major = major
        self.minor = minor
        self.patch = patch

    def short(self):
        return '{}.{}.{}'.format(self.major, self.minor, self.patch)


# originally from magic-wormhole code
def _is_non_public_numeric_address(host):
    """
    returns True if 'host' is not public
    """
    # for numeric hostnames, skip RFC1918 addresses, since no Tor exit
    # node will be able to reach those. Likewise ignore IPv6 addresses.
    try:
        a = ipaddress.ip_address(six.text_type(host))
    except ValueError:
        return False        # non-numeric, let Tor try it
    if a.is_loopback or a.is_multicast or a.is_private or a.is_reserved \
       or a.is_unspecified:
        return True         # too weird, don't connect
    return False
