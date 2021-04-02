# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import json
from datetime import datetime
from .util import NetLocation
from .util import _Version
import six
from base64 import b64encode, b64decode
from binascii import b2a_hex, a2b_hex

from twisted.internet.defer import inlineCallbacks, returnValue, succeed
from twisted.python.deprecate import deprecated
from twisted.web.client import readBody


def hexIdFromHash(thehash):
    """
    From the base-64 encoded hashes Tor uses, this produces the longer
    hex-encoded hashes.

    :param thehash: base64-encoded str
    :return: hex-encoded hash
    """
    return '$' + b2a_hex(b64decode(thehash + '=')).decode('ascii').upper()


def hashFromHexId(hexid):
    """
    From a hex fingerprint id, convert back to base-64 encoded value.
    """
    if hexid[0] == '$':
        hexid = hexid[1:]
    return b64encode(a2b_hex(hexid))[:-1].decode('ascii')


class PortRange(object):
    """
    Represents a range of ports for Router policies.
    """
    def __init__(self, a, b):
        self.min = a
        self.max = b

    def __eq__(self, b):
        return b >= self.min and b <= self.max

    def __str__(self):
        return "%d-%d" % (self.min, self.max)


class Router(object):
    """
    Represents a Tor Router, including location.

    The controller you pass in is really only used to do get_info
    calls for ip-to-country/IP in case the
    :class:`txtorcon.util.NetLocation` stuff fails to find a country.

    After an .update() call, the id_hex attribute contains a
    hex-encoded long hash (suitable, for example, to use in a
    ``GETINFO ns/id/*`` call).

    After setting the policy property you may call accepts_port() to
    find out if the router will accept a given port. This works with
    the reject or accept based policies.
    """

    def __init__(self, controller):
        self.controller = controller
        self._flags = []
        self.bandwidth = 0
        self.name_is_unique = False
        self.accepted_ports = None
        self.rejected_ports = None
        self.id_hex = None
        self._location = None
        self.from_consensus = False
        self.ip = 'unknown'
        self.ip_v6 = []                 # most routers have no IPv6 addresses

    unique_name = property(lambda x: x.name_is_unique and x.name or x.id_hex)
    "has the hex id if this router's name is not unique, or its name otherwise"

    @property
    def modified(self):
        """
        This is the time of 'the publication time of its most recent
        descriptor' (in UTC).

        See also dir-spec.txt.

        """
        # "... in the form YYYY-MM-DD HH:MM:SS, in UTC"
        if self._modified is None:
            self._modified = datetime.strptime(
                self._modified_unparsed,
                '%Y-%m-%d %H:%M:%S'
            )
        return self._modified

    def update(self, name, idhash, orhash, modified, ip, orport, dirport):
        self.name = name
        self.id_hash = idhash
        self.or_hash = orhash
        # modified is lazy-parsed, approximately doubling router-parsing time
        self._modified_unparsed = modified
        self._modified = None
        self.ip = ip
        self.or_port = orport
        self.dir_port = dirport
        self._location = None

        self.id_hex = hexIdFromHash(self.id_hash)
        # for py3, these should be valid (but *not* py2)
        # assert type(idhash) is not bytes
        # assert type(orhash) is not bytes

    def get_location(self):
        """
        Returns a Deferred that fires with a NetLocation object for this
        router.
        """
        if self._location:
            return succeed(self._location)
        if self.ip != 'unknown':
            self._location = NetLocation(self.ip)
        else:
            self._location = NetLocation(None)
        if not self._location.countrycode and self.ip != 'unknown':
            # see if Tor is magic and knows more...
            d = self.controller.get_info_raw('ip-to-country/' + self.ip)
            d.addCallback(self._set_country)
            d.addCallback(lambda _: self._location)
            return d
        return succeed(self._location)

    @property
    @deprecated(_Version("txtorcon", 18, 0, 0))
    def location(self):
        """
        A NetLocation instance with some GeoIP or pygeoip information
        about location, asn, city (if available).
        """
        if self._location:
            return self._location

        if self.ip != 'unknown':
            self._location = NetLocation(self.ip)
        else:
            self._location = NetLocation(None)
        if not self._location.countrycode and self.ip != 'unknown':
            # see if Tor is magic and knows more...
            d = self.controller.get_info_raw('ip-to-country/' + self.ip)
            d.addCallback(self._set_country)
            # ignore errors (e.g. "GeoIP Information not loaded")
            d.addErrback(lambda _: None)
        return self._location

    @property
    def flags(self):
        """
        A list of all the flags for this Router, each one an
        all-lower-case string.
        """
        return self._flags

    @flags.setter
    def flags(self, flags):
        """
        It might be nice to make flags not a list of strings. This is
        made harder by the control-spec: `...controllers MUST tolerate
        unrecognized flags and lines...`

        There is some current work in Twisted for open-ended constants
        (enums) support however, it seems.
        """
        if isinstance(flags, (six.text_type, bytes)):
            flags = flags.split()
        self._flags = [x.lower() for x in flags]
        self.name_is_unique = 'named' in self._flags

    @property
    def bandwidth(self):
        """The reported bandwidth of this Router."""
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, bw):
        self._bandwidth = int(bw)

    @inlineCallbacks
    def get_onionoo_details(self, agent):
        """
        Requests the 'details' document from onionoo.torproject.org via
        the given `twisted.web.iweb.IAgent` -- you can get a suitable
        instance to pass here by calling either :meth:`txtorcon.Tor.web_agent` or
        :meth:`txtorcon.Circuit.web_agent`.
        """

        # clearnet: 'https://onionoo.torproject.org/details?lookup={}'
        uri = 'http://tgel7v4rpcllsrk2.onion/details?lookup={}'.format(self.id_hex[1:]).encode('ascii')

        resp = yield agent.request(b'GET', uri)
        if resp.code != 200:
            raise RuntimeError(
                'Failed to lookup relay details for {}'.format(self.id_hex)
            )
        body = yield readBody(resp)
        data = json.loads(body.decode('ascii'))
        if len(data['relays']) != 1:
            raise RuntimeError(
                'Got multiple relays for {}'.format(self.id_hex)
            )
        relay_data = data['relays'][0]
        if relay_data['fingerprint'].lower() != self.id_hex[1:].lower():
            raise RuntimeError(
                'Expected "{}" but got data for "{}"'.format(self.id_hex, relay_data['fingerprint'])
            )
        returnValue(relay_data)

    # note that exit-policy is no longer included in the
    # microdescriptors by default, so this stuff is mostly here as a
    # historic artifact. If you want to use exit-policy for things
    # your best bet is to tell your tor to download full descriptors
    # (SETCONF UseMicrodescriptors 0) instead.

    @property
    def policy(self):
        """
        Port policies for this Router.
        :return: a string describing the policy
        """
        if self.accepted_ports:
            return 'accept ' + ','.join(map(str, self.accepted_ports))
        elif self.rejected_ports:
            return 'reject ' + ','.join(map(str, self.rejected_ports))
        else:
            return ''

    @policy.setter
    def policy(self, args):
        """
        setter for the policy descriptor
        """

        word = args[0]
        if word == 'reject':
            self.accepted_ports = None
            self.rejected_ports = []
            target = self.rejected_ports

        elif word == 'accept':
            self.accepted_ports = []
            self.rejected_ports = None
            target = self.accepted_ports

        else:
            raise RuntimeError("Don't understand policy word \"%s\"" % word)

        for port in args[1].split(','):
            if '-' in port:
                (a, b) = port.split('-')
                target.append(PortRange(int(a), int(b)))
            else:
                target.append(int(port))

    def accepts_port(self, port):
        """
        Query whether this Router will accept the given port.
        """

        if self.rejected_ports is None and self.accepted_ports is None:
            raise RuntimeError("policy hasn't been set yet")

        if self.rejected_ports:
            for x in self.rejected_ports:
                if port == x:
                    return False
            return True

        for x in self.accepted_ports:
            if port == x:
                return True
        return False

    def _set_country(self, c):
        """
        callback if we used Tor's GETINFO ip-to-country
        """

        self.location.countrycode = c.split()[0].split('=')[1].strip().upper()

    def __repr__(self):
        n = self.id_hex
        if self.name_is_unique:
            n = self.name
        return "<Router %s %s %s>" % (n, self.location.countrycode,
                                      self.policy)
