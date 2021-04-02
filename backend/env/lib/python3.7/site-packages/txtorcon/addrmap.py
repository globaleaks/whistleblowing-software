# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

from txtorcon.interface import IAddrListener
from txtorcon.util import maybe_ip_addr

from twisted.internet.interfaces import IReactorTime
from twisted.internet import reactor

import datetime
import shlex


class Addr(object):
    """
    One address mapping (e.g. example.com -> 127.0.0.1)
    """

    def __init__(self, map):
        """
        map is an AddrMap instance, used for scheduling expiries and
        updating the map.
        """

        self.map = map

        self.ip = None
        self.name = None
        self.expiry = None
        self.expires = None
        self.created = None

    def update(self, *args):
        """
        deals with an update from Tor; see parsing logic in torcontroller
        """

        gmtexpires = None
        (name, ip, expires) = args[:3]

        for arg in args:
            if arg.lower().startswith('expires='):
                gmtexpires = arg[8:]

        if gmtexpires is None:
            if len(args) == 3:
                gmtexpires = expires
            else:
                if args[2] == 'NEVER':
                    gmtexpires = args[2]
                else:
                    gmtexpires = args[3]

        self.name = name                # "www.example.com"
        self.ip = maybe_ip_addr(ip)     # IPV4Address instance, or string

        if self.ip == '<error>':
            self._expire()
            return

        fmt = "%Y-%m-%d %H:%M:%S"

        # if we already have expiry times, etc then we want to
        # properly delay our timeout

        oldexpires = self.expires

        if gmtexpires.upper() == 'NEVER':
            # FIXME can I just select a date 100 years in the future instead?
            self.expires = None
        else:
            self.expires = datetime.datetime.strptime(gmtexpires, fmt)
        self.created = datetime.datetime.utcnow()

        if self.expires is not None:
            if oldexpires is None:
                if self.expires <= self.created:
                    diff = datetime.timedelta(seconds=0)
                else:
                    diff = self.expires - self.created
                self.expiry = self.map.scheduler.callLater(diff.seconds,
                                                           self._expire)

            else:
                diff = self.expires - oldexpires
                self.expiry.delay(diff.seconds)

    def _expire(self):
        """
        callback done via callLater
        """
        del self.map.addr[self.name]
        self.map.notify("addrmap_expired", *[self.name], **{})


class AddrMap(object):
    """
    A collection of Addr objects mapping domains to addresses, with
    automatic expiry.

    FIXME: need listener interface, so far:

    addrmap_added(Addr)
    addrmap_expired(name)
    """
    def __init__(self):
        self.addr = {}
        self.scheduler = IReactorTime(reactor)
        self.listeners = []

    def update(self, update):
        """
        Deal with an update from Tor; either creates a new Addr object
        or find existing one and calls update() on it.
        """

        params = shlex.split(update)
        if params[0] in self.addr:
            self.addr[params[0]].update(*params)

        else:
            a = Addr(self)
            # add both name and IP address
            self.addr[params[0]] = a
            self.addr[params[1]] = a
            a.update(*params)
            self.notify("addrmap_added", *[a], **{})

    def find(self, name_or_ip):
        "FIXME should make this class a dict-like (or subclass?)"
        return self.addr[name_or_ip]

    def notify(self, method, *args, **kwargs):
        for listener in self.listeners:
            getattr(listener, method)(*args, **kwargs)

    def add_listener(self, listener):
        if listener not in self.listeners:
            self.listeners.append(IAddrListener(listener))
