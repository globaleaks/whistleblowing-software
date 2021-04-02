# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import functools
from twisted.internet import defer

from txtorcon.interface import ITorControlProtocol


class MagicContainer(object):
    """
    This merely contains 1 or more methods or further MagicContainer
    instances; see _do_setup in TorInfo.

    Once _setup_complete() is called, this behaves differently so that
    one can get nicer access to GETINFO things from TorInfo --
    specifically dir() and so forth pretend that there are only
    methods/attributes that pertain to actual Tor GETINFO keys.

    See TorInfo.
    """

    def __init__(self, n):
        self._txtorcon_name = n
        self.attrs = {}
        self._setup = False

    def _setup_complete(self):
        self._setup = True

    def _add_attribute(self, n, v):
        self.attrs[n] = v

    def __repr__(self):
        return object.__getattribute__(self, '_txtorcon_name')

    def __getitem__(self, idx):
        return list(object.__getattribute__(self, 'attrs').items())[idx][1]

    def __len__(self):
        return len(object.__getattribute__(self, 'attrs'))

    def __dir__(self):
        return list(object.__getattribute__(self, 'attrs').keys())

    def __getattribute__(self, name):
        sup = super(MagicContainer, self)
        if sup.__getattribute__('_setup') is False:
            return sup.__getattribute__(name)

        attrs = sup.__getattribute__('attrs')
        if name == '__members__':
            return list(attrs.keys())

        else:
            if name.startswith('__'):
                return sup.__getattribute__(name)

            try:
                return attrs[name]
            except KeyError:
                if name in ['dump']:
                    return object.__getattribute__(self, name)
                raise AttributeError(name)

    def dump(self, prefix):
        prefix = prefix + '.' + object.__getattribute__(self, '_txtorcon_name')
        for x in list(object.__getattribute__(self, 'attrs').values()):
            x.dump(prefix)


class ConfigMethod(object):
    def __init__(self, info_key, protocol, takes_arg=False):
        self.info_key = info_key
        self.proto = protocol
        self.takes_arg = takes_arg

    def dump(self, prefix):
        n = self.info_key.replace('/', '.')
        n = n.replace('-', '_')
        s = '%s(%s)' % (n, 'arg' if self.takes_arg else '')
        return s

    def __call__(self, *args):
        if self.takes_arg:
            if len(args) != 1:
                raise TypeError(
                    '"%s" takes exactly one argument' % self.info_key
                )
            req = '%s/%s' % (self.info_key, str(args[0]))

        else:
            if len(args) != 0:
                raise TypeError('"%s" takes no arguments' % self.info_key)

            req = self.info_key

        def stripper(key, arg):
            # strip "keyname="
            # sometimes keyname= is followed by a newline, so final .strip()
            return arg.strip()[len(key) + 1:].strip()

        d = self.proto.get_info_raw(req)
        d.addCallback(functools.partial(stripper, req))
        return d

    def __str__(self):
        arg = ''
        if self.takes_arg:
            arg = 'arg'
        return '%s(%s)' % (self.info_key.replace('-', '_'), arg)


class TorInfo(object):
    """Implements some attribute magic over top of TorControlProtocol so
    that all the available GETINFO values are gettable in a little
    easier fashion. Dashes are replaced by underscores (since dashes
    aren't valid in method/attribute names for Python). Some of the
    magic methods will take a single string argument if the
    corresponding Tor GETINFO would take one (in 'GETINFO info/names'
    it will end with '/*', and the same in torspec). In either case,
    the method returns a Deferred which will callback with the
    requested value, always a string.

    For example (see also examples/tor_info.py):

        proto = TorControlProtocol()
        #...
        def cb(arg):
            print arg
        info = TorInfo(proto)
        info.traffic.written().addCallback(cb)
        info.ip_to_country('8.8.8.8').addCallback(cb)

    For interactive use -- or even checking things progammatically --
    TorInfo pretends it only has attributes that coorespond to valid
    GETINFO calls.  So for example, dir(info) will only return all the
    currently valid top-level things. In the above example this might
    be ['traffic', 'ip_to_country'] (of course in practice this is a
    much longer list). And "dir(info.traffic)" might return ['read',
    'written']

    For something similar to this for configuration (GETCONF, SETCONF)
    see TorConfig which is quite a lot more complicated (internally)
    since you can set config items.

    NOTE that 'GETINFO config/*' is not supported as it's the only
    case that's not a leaf, but theoretically a method.

    """

    def __init__(self, control, errback=None):
        self._setup = False
        self.attrs = {}
        '''After _setup is True, these are all we show as attributes.'''

        self.protocol = ITorControlProtocol(control)
        self.errback = errback

        self.post_bootstrap = defer.Deferred()
        if self.protocol.post_bootstrap:
            self.protocol.post_bootstrap.addCallback(self.bootstrap)

        else:
            self.bootstrap()

    def _add_attribute(self, n, v):
        self.attrs[n] = v

    # iterator protocol

    def __getitem__(self, idx):
        sup = super(TorInfo, self)
        if sup.__getattribute__('_setup') is True:
            return list(object.__getattribute__(self, 'attrs').items())[idx][1]
        raise TypeError("No __getitem__ until we've setup.")

    def __len__(self):
        sup = super(TorInfo, self)
        if sup.__getattribute__('_setup') is True:
            return len(object.__getattribute__(self, 'attrs'))
        raise TypeError("No length until we're setup.")

    # change our attribute behavior based on the value of _setup

    def __dir__(self):
        sup = super(TorInfo, self)
        if sup.__getattribute__('_setup') is True:
            return list(sup.__getattribute__('attrs').keys())
        return list(sup.__getattribute__('__dict__').keys())

    def __getattribute__(self, name):
        sup = super(TorInfo, self)
        if sup.__getattribute__('_setup') is False:
            return sup.__getattribute__(name)

        attrs = sup.__getattribute__('attrs')
        if name == '__members__':
            return list(attrs.keys())

        else:
            try:
                return attrs[name]

            except KeyError:
                if name == 'dump':
                    return object.__getattribute__(self, name)

        raise AttributeError(name)

    def bootstrap(self, *args):
        d = self.protocol.get_info_raw("info/names")
        d.addCallback(self._do_setup)
        if self.errback:
            d.addErrback(self.errback)
        d.addCallback(self._setup_complete)
        return d

    def dump(self):
        for x in object.__getattribute__(self, 'attrs').values():
            x.dump('')

    def _do_setup(self, data):
        # FIXME figure out why network-status doesn't work (get
        # nothing back from Tor it seems, although stem does get an
        # answer). this is a space-separated list of ~2500 OR id's;
        # could it be that LineReceiver can't handle it?
        added_magic = []
        for line in data.split('\n'):
            if line == "info/names=" or line.strip() == '':
                continue

            (name, documentation) = line.split(' ', 1)
            # FIXME think about this -- this is the only case where
            # there's something that's a directory
            # (i.e. MagicContainer) AND needs to be a ConfigMethod as
            # well...but doesn't really seem very useful. Somewhat
            # simpler to not support this case for now...
            if name == 'config/*':
                continue

            if name.endswith('/*'):
                # this takes an arg, so make a method
                bits = name[:-2].split('/')
                takes_arg = True

            else:
                bits = name.split('/')
                takes_arg = False

            mine = self
            for bit in bits[:-1]:
                bit = bit.replace('-', '_')
                if bit in mine.attrs:
                    mine = mine.attrs[bit]
                    if not isinstance(mine, MagicContainer):
                        raise RuntimeError(
                            "Already had something: %s for %s" % (bit, name)
                        )

                else:
                    c = MagicContainer(bit)
                    added_magic.append(c)
                    mine._add_attribute(bit, c)
                    mine = c
            n = bits[-1].replace('-', '_')
            if n in mine.attrs:
                raise RuntimeError(
                    "Already had something: %s for %s" % (n, name)
                )
            mine._add_attribute(n, ConfigMethod('/'.join(bits),
                                                self.protocol, takes_arg))

        for c in added_magic:
            c._setup_complete()
        return None

    def _setup_complete(self, *args):
        pb = self.post_bootstrap
        self._setup = True
        pb.callback(self)
