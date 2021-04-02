# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import os
import re
import six
import functools
import warnings
from io import StringIO
from collections import OrderedDict
from warnings import warn

from twisted.python import log
from twisted.python.compat import nativeString
from twisted.python.deprecate import deprecated
from twisted.internet import defer
from twisted.internet.endpoints import TCP4ClientEndpoint, UNIXClientEndpoint

from txtorcon.torcontrolprotocol import parse_keywords, DEFAULT_VALUE
from txtorcon.torcontrolprotocol import TorProtocolError
from txtorcon.interface import ITorControlProtocol
from txtorcon.util import find_keywords
from .onion import IOnionClient, FilesystemOnionService, FilesystemAuthenticatedOnionService
from .onion import DISCARD
from .onion import AuthStealth, AuthBasic
from .onion import EphemeralOnionService
from .onion import _await_descriptor_upload
from .onion import _parse_client_keys
from .util import _Version


@defer.inlineCallbacks
@deprecated(_Version("txtorcon", 0, 18, 0))
def launch_tor(config, reactor,
               tor_binary=None,
               progress_updates=None,
               connection_creator=None,
               timeout=None,
               kill_on_stderr=True,
               stdout=None, stderr=None):
    """
    Deprecated; use launch() instead.

    See also controller.py
    """
    from .controller import launch
    # XXX FIXME are we dealing with options in the config "properly"
    # as far as translating semantics from the old launch_tor to
    # launch()? DataDirectory, User, ControlPort, ...?
    tor = yield launch(
        reactor,
        stdout=stdout,
        stderr=stderr,
        progress_updates=progress_updates,
        tor_binary=tor_binary,
        connection_creator=connection_creator,
        timeout=timeout,
        kill_on_stderr=kill_on_stderr,
        _tor_config=config,
    )
    defer.returnValue(tor.process)


class TorConfigType(object):
    """
    Base class for all configuration types, which function as parsers
    and un-parsers.
    """

    def parse(self, s):
        """
        Given the string s, this should return a parsed representation
        of it.
        """
        return s

    def validate(self, s, instance, name):
        """
        If s is not a valid type for this object, an exception should
        be thrown. The validated object should be returned.
        """
        return s


class Boolean(TorConfigType):
    "Boolean values are stored as 0 or 1."
    def parse(self, s):
        if int(s):
            return True
        return False

    def validate(self, s, instance, name):
        if s:
            return 1
        return 0


class Boolean_Auto(TorConfigType):
    """
    weird class-name, but see the parser for these which is *mostly*
    just the classname <==> string from Tor, except for something
    called Boolean+Auto which is replace()d to be Boolean_Auto
    """

    def parse(self, s):
        if s == 'auto' or int(s) < 0:
            return -1
        if int(s):
            return 1
        return 0

    def validate(self, s, instance, name):
        # FIXME: Is 'auto' an allowed value? (currently not)
        s = int(s)
        if s < 0:
            return 'auto'
        elif s:
            return 1
        else:
            return 0


class Integer(TorConfigType):
    def parse(self, s):
        return int(s)

    def validate(self, s, instance, name):
        return int(s)


class SignedInteger(Integer):
    pass


class Port(Integer):
    pass


class TimeInterval(Integer):
    pass


# not actually used?
class TimeMsecInterval(TorConfigType):
    pass


class DataSize(Integer):
    pass


class Float(TorConfigType):
    def parse(self, s):
        return float(s)


# unused also?
class Time(TorConfigType):
    pass


class CommaList(TorConfigType):
    def parse(self, s):
        return [x.strip() for x in s.split(',')]


# FIXME: in latest master; what is it?
# Tor source says "A list of strings, separated by commas and optional
# whitespace, representing intervals in seconds, with optional units"
class TimeIntervalCommaList(CommaList):
    pass


# FIXME: is this really a comma-list?
class RouterList(CommaList):
    pass


class String(TorConfigType):
    pass


class Filename(String):
    pass


class LineList(TorConfigType):
    def parse(self, s):
        if isinstance(s, list):
            return [str(x).strip() for x in s]
        return [x.strip() for x in s.split('\n')]

    def validate(self, obj, instance, name):
        if not isinstance(obj, list):
            raise ValueError("Not valid for %s: %s" % (self.__class__, obj))
        return _ListWrapper(
            obj, functools.partial(instance.mark_unsaved, name))


config_types = [Boolean, Boolean_Auto, LineList, Integer, SignedInteger, Port,
                TimeInterval, TimeMsecInterval,
                DataSize, Float, Time, CommaList, String, LineList, Filename,
                RouterList, TimeIntervalCommaList]


def is_list_config_type(klass):
    return 'List' in klass.__name__ or klass.__name__ in ['HiddenServices']


def _wrapture(orig):
    """
    Returns a new method that wraps orig (the original method) with
    something that first calls on_modify from the
    instance. _ListWrapper uses this to wrap all methods that modify
    the list.
    """

#    @functools.wraps(orig)
    def foo(*args):
        obj = args[0]
        obj.on_modify()
        return orig(*args)
    return foo


class _ListWrapper(list):
    """
    Do some voodoo to wrap lists so that if you do anything to modify
    it, we mark the config as needing saving.

    FIXME: really worth it to preserve attribute-style access? seems
    to be okay from an exterior API perspective....
    """

    def __init__(self, thelist, on_modify_cb):
        list.__init__(self, thelist)
        self.on_modify = on_modify_cb

    __setitem__ = _wrapture(list.__setitem__)
    append = _wrapture(list.append)
    extend = _wrapture(list.extend)
    insert = _wrapture(list.insert)
    remove = _wrapture(list.remove)
    pop = _wrapture(list.pop)

    def __repr__(self):
        return '_ListWrapper' + super(_ListWrapper, self).__repr__()


if six.PY2:
    setattr(_ListWrapper, '__setslice__', _wrapture(list.__setslice__))


class HiddenService(object):
    """
    Because hidden service configuration is handled specially by Tor,
    we wrap the config in this class. This corresponds to the
    HiddenServiceDir, HiddenServicePort, HiddenServiceVersion and
    HiddenServiceAuthorizeClient lines from the config. If you want
    multiple HiddenServicePort lines, simply append more strings to
    the ports member.

    To create an additional hidden service, append a new instance of
    this class to the config (ignore the conf argument)::

        state.hiddenservices.append(HiddenService('/path/to/dir', ['80 127.0.0.1:1234']))
    """

    def __init__(self, config, thedir, ports,
                 auth=[], ver=2, group_readable=0):
        """
        config is the TorConfig to which this will belong, thedir
        corresponds to 'HiddenServiceDir' and will ultimately contain
        a 'hostname' and 'private_key' file, ports is a list of lines
        corresponding to HiddenServicePort (like '80 127.0.0.1:1234'
        to advertise a hidden service at port 80 and redirect it
        internally on 127.0.0.1:1234). auth corresponds to the
        HiddenServiceAuthenticateClient lines and can be either a
        string or a list of strings (like 'basic client0,client1' or
        'stealth client5,client6') and ver corresponds to
        HiddenServiceVersion and is always 2 right now.

        XXX FIXME can we avoid having to pass the config object
        somehow? Like provide a factory-function on TorConfig for
        users instead?
        """

        self.conf = config
        self.dir = thedir
        self.version = ver
        self.group_readable = group_readable

        # lazy-loaded if the @properties are accessed
        self._private_key = None
        self._clients = None
        self._hostname = None
        self._client_keys = None

        # HiddenServiceAuthorizeClient is a list
        # in case people are passing '' for the auth
        if not auth:
            auth = []
        elif not isinstance(auth, list):
            auth = [auth]
        self.authorize_client = _ListWrapper(
            auth, functools.partial(
                self.conf.mark_unsaved, 'HiddenServices'
            )
        )

        # there are three magic attributes, "hostname" and
        # "private_key" are gotten from the dir if they're still None
        # when accessed. "client_keys" parses out any client
        # authorizations. Note that after a SETCONF has returned '250
        # OK' it seems from tor code that the keys will always have
        # been created on disk by that point

        if not isinstance(ports, list):
            ports = [ports]
        self.ports = _ListWrapper(ports, functools.partial(
            self.conf.mark_unsaved, 'HiddenServices'))

    def __setattr__(self, name, value):
        """
        We override the default behavior so that we can mark
        HiddenServices as unsaved in our TorConfig object if anything
        is changed.
        """
        watched_params = ['dir', 'version', 'authorize_client', 'ports']
        if name in watched_params and self.conf:
            self.conf.mark_unsaved('HiddenServices')
        if isinstance(value, list):
            value = _ListWrapper(value, functools.partial(
                self.conf.mark_unsaved, 'HiddenServices'))
        self.__dict__[name] = value

    @property
    def private_key(self):
        if self._private_key is None:
            with open(os.path.join(self.dir, 'private_key')) as f:
                self._private_key = f.read().strip()
        return self._private_key

    @property
    def clients(self):
        if self._clients is None:
            self._clients = []
            try:
                with open(os.path.join(self.dir, 'hostname')) as f:
                    for line in f.readlines():
                        args = line.split()
                        # XXX should be a dict?
                        if len(args) > 1:
                            # tag, onion-uri?
                            self._clients.append((args[0], args[1]))
                        else:
                            self._clients.append(('default', args[0]))
            except IOError:
                pass
        return self._clients

    @property
    def hostname(self):
        if self._hostname is None:
            with open(os.path.join(self.dir, 'hostname')) as f:
                data = f.read().strip()
            host = None
            for line in data.split('\n'):
                h = line.split(' ')[0]
                if host is None:
                    host = h
                elif h != host:
                    raise RuntimeError(
                        ".hostname accessed on stealth-auth'd hidden-service "
                        "with multiple onion addresses."
                    )
            self._hostname = h
        return self._hostname

    @property
    def client_keys(self):
        if self._client_keys is None:
            fname = os.path.join(self.dir, 'client_keys')
            self._client_keys = []
            if os.path.exists(fname):
                with open(fname) as f:
                    self._client_keys = _parse_client_keys(f)
        return self._client_keys

    def config_attributes(self):
        """
        Helper method used by TorConfig when generating a torrc file.
        """

        rtn = [('HiddenServiceDir', str(self.dir))]
        if self.conf._supports['HiddenServiceDirGroupReadable'] \
           and self.group_readable:
            rtn.append(('HiddenServiceDirGroupReadable', str(1)))
        for port in self.ports:
            rtn.append(('HiddenServicePort', str(port)))
        if self.version:
            rtn.append(('HiddenServiceVersion', str(self.version)))
        for authline in self.authorize_client:
            rtn.append(('HiddenServiceAuthorizeClient', str(authline)))
        return rtn


def _is_valid_keyblob(key_blob_or_type):
    try:
        key_blob_or_type = nativeString(key_blob_or_type)
    except (UnicodeError, TypeError):
        return False
    else:
        return re.match(r'[^ :]+:[^ :]+$', key_blob_or_type)


# we can't use @deprecated here because then you can't use the
# resulting class in isinstance() things and the like, because Twisted
# makes it into a function instead :( so we @deprecate __init__ for now
# @deprecated(_Version("txtorcon", 18, 0, 0))
class EphemeralHiddenService(object):
    '''
    Deprecated as of 18.0.0. Please instead use :class:`txtorcon.EphemeralOnionService`

    This uses the ephemeral hidden-service APIs (in comparison to
    torrc or SETCONF). This means your hidden-service private-key is
    never in a file. It also means that when the process exits, that
    HS goes away. See documentation for ADD_ONION in torspec:
    https://gitweb.torproject.org/torspec.git/tree/control-spec.txt#n1295
    '''

    @deprecated(_Version("txtorcon", 18, 0, 0))
    def __init__(self, ports, key_blob_or_type='NEW:BEST', auth=[], ver=2):
        # deprecated; use Tor.create_onion_service
        warn(
            'EphemeralHiddenService is deprecated; use EphemeralOnionService instead',
            DeprecationWarning,
        )
        if _is_valid_keyblob(key_blob_or_type):
            self._key_blob = nativeString(key_blob_or_type)
        else:
            raise ValueError(
                'key_blob_or_type must be a string in the formats '
                '"NEW:<ALGORITHM>" or "<ALGORITHM>:<KEY>"')
        if isinstance(ports, (six.text_type, str)):
            ports = [ports]
        self._ports = [x.replace(' ', ',') for x in ports]
        self._keyblob = key_blob_or_type
        self.auth = auth  # FIXME ununsed
        # FIXME nicer than assert, plz
        self.version = ver
        self.hostname = None

    @defer.inlineCallbacks
    def add_to_tor(self, protocol):
        '''
        Returns a Deferred which fires with 'self' after at least one
        descriptor has been uploaded. Errback if no descriptor upload
        succeeds.
        '''

        upload_d = _await_descriptor_upload(protocol, self, progress=None, await_all_uploads=False)

        # _add_ephemeral_service takes a TorConfig but we don't have
        # that here ..  and also we're just keeping this for
        # backwards-compatability anyway so instead of trying to
        # re-use that helper I'm leaving this original code here. So
        # this is what it supports and that's that:
        ports = ' '.join(map(lambda x: 'Port=' + x.strip(), self._ports))
        cmd = 'ADD_ONION %s %s' % (self._key_blob, ports)
        ans = yield protocol.queue_command(cmd)
        ans = find_keywords(ans.split('\n'))
        self.hostname = ans['ServiceID'] + '.onion'
        if self._key_blob.startswith('NEW:'):
            self.private_key = ans['PrivateKey']
        else:
            self.private_key = self._key_blob

        log.msg('Created hidden-service at', self.hostname)

        log.msg("Created '{}', waiting for descriptor uploads.".format(self.hostname))
        yield upload_d

    @defer.inlineCallbacks
    def remove_from_tor(self, protocol):
        '''
        Returns a Deferred which fires with None
        '''
        r = yield protocol.queue_command('DEL_ONION %s' % self.hostname[:-6])
        if r.strip() != 'OK':
            raise RuntimeError('Failed to remove hidden service: "%s".' % r)


def _endpoint_from_socksport_line(reactor, socks_config):
    """
    Internal helper.

    Returns an IStreamClientEndpoint for the given config, which is of
    the same format expected by the SOCKSPort option in Tor.
    """
    if socks_config.startswith('unix:'):
        # XXX wait, can SOCKSPort lines with "unix:/path" still
        # include options afterwards? What about if the path has a
        # space in it?
        return UNIXClientEndpoint(reactor, socks_config[5:])

    # options like KeepAliveIsolateSOCKSAuth can be appended
    # to a SocksPort line...
    if ' ' in socks_config:
        socks_config = socks_config.split()[0]
    if ':' in socks_config:
        host, port = socks_config.split(':', 1)
        port = int(port)
    else:
        host = '127.0.0.1'
        port = int(socks_config)
    return TCP4ClientEndpoint(reactor, host, port)


class TorConfig(object):
    """This class abstracts out Tor's config, and can be used both to
    create torrc files from nothing and track live configuration of a Tor
    instance.

    Also, it gives easy access to all the configuration options
    present. This is initialized at "bootstrap" time, providing
    attribute-based access thereafter. Note that after you set some
    number of items, you need to do a save() before these are sent to
    Tor (and then they will be done as one SETCONF).

    You may also use this class to construct a configuration from
    scratch (e.g. to give to :func:`txtorcon.launch_tor`). In this
    case, values are reflected right away. (If we're not bootstrapped
    to a Tor, this is the mode).

    Note that you do not need to call save() if you're just using
    TorConfig to create a .torrc file or for input to launch_tor().

    This class also listens for CONF_CHANGED events to update the
    cached data in the event other controllers (etc) changed it.

    There is a lot of magic attribute stuff going on in here (which
    might be a bad idea, overall) but the *intent* is that you can
    just set Tor options and it will all Just Work. For config items
    that take multiple values, set that to a list. For example::

        conf = TorConfig(...)
        conf.SOCKSPort = [9050, 1337]
        conf.HiddenServices.append(HiddenService(...))

    (Incoming objects, like lists, are intercepted and wrapped).

    FIXME: when is CONF_CHANGED introduced in Tor? Can we do anything
    like it for prior versions?

    FIXME:

        - HiddenServiceOptions is special: GETCONF on it returns
          several (well, two) values. Besides adding the two keys 'by
          hand' do we need to do anything special? Can't we just depend
          on users doing 'conf.hiddenservicedir = foo' AND
          'conf.hiddenserviceport = bar' before a save() ?

        - once I determine a value is default, is there any way to
          actually get what this value is?

    """

    @staticmethod
    @defer.inlineCallbacks
    def from_protocol(proto):
        """
        This creates and returns a ready-to-go TorConfig instance from the
        given protocol, which should be an instance of
        TorControlProtocol.
        """
        cfg = TorConfig(control=proto)
        yield cfg.post_bootstrap
        defer.returnValue(cfg)

    def __init__(self, control=None):
        self.config = {}
        '''Current configuration, by keys.'''

        if control is None:
            self._protocol = None
            self.__dict__['_accept_all_'] = None

        else:
            self._protocol = ITorControlProtocol(control)

        self.unsaved = OrderedDict()
        '''Configuration that has been changed since last save().'''

        self.parsers = {}
        '''Instances of the parser classes, subclasses of TorConfigType'''

        self.list_parsers = set(['hiddenservices', 'ephemeralonionservices'])
        '''All the names (keys from .parsers) that are a List of something.'''

        # during bootstrapping we decide whether we support the
        # following features. A thing goes in here if TorConfig
        # behaves differently depending upon whether it shows up in
        # "GETINFO config/names"
        self._supports = dict(
            HiddenServiceDirGroupReadable=False
        )
        self._defaults = dict()

        self.post_bootstrap = defer.Deferred()
        if self.protocol:
            if self.protocol.post_bootstrap:
                self.protocol.post_bootstrap.addCallback(
                    self.bootstrap).addErrback(self.post_bootstrap.errback)
            else:
                self.bootstrap()

        else:
            self.do_post_bootstrap(self)

        self.__dict__['_setup_'] = None

    def socks_endpoint(self, reactor, port=None):
        """
        Returns a TorSocksEndpoint configured to use an already-configured
        SOCKSPort from the Tor we're connected to. By default, this
        will be the very first SOCKSPort.

        :param port: a str, the first part of the SOCKSPort line (that
            is, a port like "9151" or a Unix socket config like
            "unix:/path". You may also specify a port as an int.

        If you need to use a particular port that may or may not
        already be configured, see the async method
        :meth:`txtorcon.TorConfig.create_socks_endpoint`
        """

        if len(self.SocksPort) == 0:
            raise RuntimeError(
                "No SOCKS ports configured"
            )

        socks_config = None
        if port is None:
            socks_config = self.SocksPort[0]
        else:
            port = str(port)  # in case e.g. an int passed in
            if ' ' in port:
                raise ValueError(
                    "Can't specify options; use create_socks_endpoint instead"
                )

            for idx, port_config in enumerate(self.SocksPort):
                # "SOCKSPort" is a gnarly beast that can have a bunch
                # of options appended, so we have to split off the
                # first thing which *should* be the port (or can be a
                # string like 'unix:')
                if port_config.split()[0] == port:
                    socks_config = port_config
                    break
        if socks_config is None:
            raise RuntimeError(
                "No SOCKSPort configured for port {}".format(port)
            )

        return _endpoint_from_socksport_line(reactor, socks_config)

    @defer.inlineCallbacks
    def create_socks_endpoint(self, reactor, socks_config):
        """
        Creates a new TorSocksEndpoint instance given a valid
        configuration line for ``SocksPort``; if this configuration
        isn't already in the underlying tor, we add it. Note that this
        method may call :meth:`txtorcon.TorConfig.save()` on this instance.

        Note that calling this with `socks_config=None` is equivalent
        to calling `.socks_endpoint` (which is not async).

        XXX socks_config should be .. i dunno, but there's fucking
        options and craziness, e.g. default Tor Browser Bundle is:
        ['9150 IPv6Traffic PreferIPv6 KeepAliveIsolateSOCKSAuth',
        '9155']

        XXX maybe we should say "socks_port" as the 3rd arg, insist
        it's an int, and then allow/support all the other options
        (e.g. via kwargs)

        XXX we could avoid the "maybe call .save()" thing; worth it?
        (actually, no we can't or the Tor won't have it config'd)
        """

        yield self.post_bootstrap

        if socks_config is None:
            if len(self.SocksPort) == 0:
                raise RuntimeError(
                    "socks_port is None and Tor has no SocksPorts configured"
                )
            socks_config = self.SocksPort[0]
        else:
            if not any([socks_config in port for port in self.SocksPort]):
                # need to configure Tor
                self.SocksPort.append(socks_config)
                try:
                    yield self.save()
                except TorProtocolError as e:
                    extra = ''
                    if socks_config.startswith('unix:'):
                        # XXX so why don't we check this for the
                        # caller, earlier on?
                        extra = '\nNote Tor has specific ownership/permissions ' +\
                                'requirements for unix sockets and parent dir.'
                    raise RuntimeError(
                        "While configuring SOCKSPort to '{}', error from"
                        " Tor: {}{}".format(
                            socks_config, e, extra
                        )
                    )

        defer.returnValue(
            _endpoint_from_socksport_line(reactor, socks_config)
        )

    # FIXME should re-name this to "tor_protocol" to be consistent
    # with other things? Or rename the other things?
    """
    read-only access to TorControlProtocol. Call attach_protocol() to
    set it, which can only be done if we don't already have a
    protocol.
    """
    def _get_protocol(self):
        return self.__dict__['_protocol']
    protocol = property(_get_protocol)
    tor_protocol = property(_get_protocol)

    def attach_protocol(self, proto):
        """
        returns a Deferred that fires once we've set this object up to
        track the protocol. Fails if we already have a protocol.
        """
        if self._protocol is not None:
            raise RuntimeError("Already have a protocol.")
        # make sure we have nothing in self.unsaved
        self.save()
        self.__dict__['_protocol'] = proto

        # FIXME some of this is duplicated from ctor
        del self.__dict__['_accept_all_']
        self.__dict__['post_bootstrap'] = defer.Deferred()
        if proto.post_bootstrap:
            proto.post_bootstrap.addCallback(self.bootstrap)
        return self.__dict__['post_bootstrap']

    def __setattr__(self, name, value):
        """
        we override this so that we can provide direct attribute
        access to our config items, and move them into self.unsaved
        when they've been changed. hiddenservices have to be special
        unfortunately. the _setup_ thing is so that we can set up the
        attributes we need in the constructor without uusing __dict__
        all over the place.
        """

        # appease flake8's hatred of lambda :/
        def has_setup_attr(o):
            return '_setup_' in o.__dict__

        def has_accept_all_attr(o):
            return '_accept_all_' in o.__dict__

        def is_hidden_services(s):
            return s.lower() == "hiddenservices"

        if has_setup_attr(self):
            name = self._find_real_name(name)
            if not has_accept_all_attr(self) and not is_hidden_services(name):
                value = self.parsers[name].validate(value, self, name)
            if isinstance(value, list):
                value = _ListWrapper(
                    value, functools.partial(self.mark_unsaved, name))

            name = self._find_real_name(name)
            self.unsaved[name] = value

        else:
            super(TorConfig, self).__setattr__(name, value)

    def _maybe_create_listwrapper(self, rn):
        if rn.lower() in self.list_parsers and rn not in self.config:
            self.config[rn] = _ListWrapper([], functools.partial(
                self.mark_unsaved, rn))

    def __getattr__(self, name):
        """
        on purpose, we don't return self.unsaved if the key is in there
        because I want the config to represent the running Tor not
        ``things which might get into the running Tor if save() were
        to be called''
        """
        rn = self._find_real_name(name)
        if '_accept_all_' in self.__dict__ and rn in self.unsaved:
            return self.unsaved[rn]
        self._maybe_create_listwrapper(rn)
        v = self.config[rn]
        if v == DEFAULT_VALUE:
            v = self.__dict__['_defaults'].get(rn, DEFAULT_VALUE)
        return v

    def __contains__(self, item):
        if item in self.unsaved and '_accept_all_' in self.__dict__:
            return True
        return item in self.config

    def __iter__(self):
        '''
        FIXME needs proper iterator tests in test_torconfig too
        '''
        for x in self.config.__iter__():
            yield x
        for x in self.__dict__['unsaved'].__iter__():
            yield x

    def get_type(self, name):
        """
        return the type of a config key.

        :param: name the key

        FIXME can we do something more-clever than this for client
        code to determine what sort of thing a key is?
        """

        # XXX FIXME uhm...how to do all the different types of hidden-services?
        if name.lower() == 'hiddenservices':
            return FilesystemOnionService
        return type(self.parsers[name])

    def _conf_changed(self, arg):
        """
        internal callback. from control-spec:

        4.1.18. Configuration changed

          The syntax is:
             StartReplyLine *(MidReplyLine) EndReplyLine

             StartReplyLine = "650-CONF_CHANGED" CRLF
             MidReplyLine = "650-" KEYWORD ["=" VALUE] CRLF
             EndReplyLine = "650 OK"

          Tor configuration options have changed (such as via a SETCONF or
          RELOAD signal). KEYWORD and VALUE specify the configuration option
          that was changed.  Undefined configuration options contain only the
          KEYWORD.
        """

        conf = parse_keywords(arg, multiline_values=False)
        for (k, v) in conf.items():
            # v will be txtorcon.DEFAULT_VALUE already from
            # parse_keywords if it was unspecified
            real_name = self._find_real_name(k)
            if real_name in self.parsers:
                v = self.parsers[real_name].parse(v)
            self.config[real_name] = v

    def bootstrap(self, arg=None):
        '''
        This only takes args so it can be used as a callback. Don't
        pass an arg, it is ignored.
        '''
        try:
            d = self.protocol.add_event_listener(
                'CONF_CHANGED', self._conf_changed)
        except RuntimeError:
            # for Tor versions which don't understand CONF_CHANGED
            # there's nothing we can really do.
            log.msg(
                "Can't listen for CONF_CHANGED event; won't stay up-to-date "
                "with other clients.")
            d = defer.succeed(None)
        d.addCallback(lambda _: self.protocol.get_info_raw("config/names"))
        d.addCallback(self._do_setup)
        d.addCallback(self.do_post_bootstrap)
        d.addErrback(self.do_post_errback)

    def do_post_errback(self, f):
        self.post_bootstrap.errback(f)
        return None

    def do_post_bootstrap(self, arg):
        if not self.post_bootstrap.called:
            self.post_bootstrap.callback(self)
        return self

    def needs_save(self):
        return len(self.unsaved) > 0

    def mark_unsaved(self, name):
        name = self._find_real_name(name)
        if name in self.config and name not in self.unsaved:
            self.unsaved[name] = self.config[self._find_real_name(name)]

    def save(self):
        """
        Save any outstanding items. This returns a Deferred which will
        errback if Tor was unhappy with anything, or callback with
        this TorConfig object on success.
        """

        if not self.needs_save():
            return defer.succeed(self)

        args = []
        directories = []
        for (key, value) in self.unsaved.items():
            if key == 'HiddenServices':
                self.config['HiddenServices'] = value
                # using a list here because at least one unit-test
                # cares about order -- and conceivably order *could*
                # matter here, to Tor...
                services = list()
                # authenticated services get flattened into the HiddenServices list...
                for hs in value:
                    if IOnionClient.providedBy(hs):
                        parent = IOnionClient(hs).parent
                        if parent not in services:
                            services.append(parent)
                    elif isinstance(hs, (EphemeralOnionService, EphemeralHiddenService)):
                        raise ValueError(
                            "Only filesystem based Onion services may be added"
                            " via TorConfig.hiddenservices; ephemeral services"
                            " must be created with 'create_onion_service'."
                        )
                    else:
                        if hs not in services:
                            services.append(hs)

                for hs in services:
                    for (k, v) in hs.config_attributes():
                        if k == 'HiddenServiceDir':
                            if v not in directories:
                                directories.append(v)
                                args.append(k)
                                args.append(v)
                            else:
                                raise RuntimeError("Trying to add hidden service with same HiddenServiceDir: %s" % v)
                        else:
                            args.append(k)
                            args.append(v)
                continue

            if isinstance(value, list):
                for x in value:
                    # FIXME XXX
                    if x is not DEFAULT_VALUE:
                        args.append(key)
                        args.append(str(x))

            else:
                args.append(key)
                args.append(value)

            # FIXME in future we should wait for CONF_CHANGED and
            # update then, right?
            real_name = self._find_real_name(key)
            if not isinstance(value, list) and real_name in self.parsers:
                value = self.parsers[real_name].parse(value)
            self.config[real_name] = value

        # FIXME might want to re-think this, but currently there's no
        # way to put things into a config and get them out again
        # nicely...unless you just don't assign a protocol
        if self.protocol:
            d = self.protocol.set_conf(*args)
            d.addCallback(self._save_completed)
            return d

        else:
            self._save_completed()
            return defer.succeed(self)

    def _save_completed(self, *args):
        '''internal callback'''
        self.__dict__['unsaved'] = {}
        return self

    def _find_real_name(self, name):
        keys = list(self.__dict__['parsers'].keys()) + list(self.__dict__['config'].keys())
        for x in keys:
            if x.lower() == name.lower():
                return x
        return name

    @defer.inlineCallbacks
    def _get_defaults(self):
        try:
            defaults_raw = yield self.protocol.get_info_raw("config/defaults")
            defaults = {}
            for line in defaults_raw.split('\n')[1:]:
                k, v = line.split(' ', 1)
                if k in defaults:
                    if isinstance(defaults[k], list):
                        defaults[k].append(v)
                    else:
                        defaults[k] = [defaults[k], v]
                else:
                    defaults[k] = v
        except TorProtocolError:
            # must be a version of Tor without config/defaults
            defaults = dict()
        defer.returnValue(defaults)

    @defer.inlineCallbacks
    def _do_setup(self, data):
        defaults = self.__dict__['_defaults'] = yield self._get_defaults()

        for line in data.split('\n'):
            if line == "config/names=":
                continue

            (name, value) = line.split()
            if name in self._supports:
                self._supports[name] = True

            if name == 'HiddenServiceOptions':
                # set up the "special-case" hidden service stuff
                servicelines = yield self.protocol.get_conf_raw(
                    'HiddenServiceOptions')
                self._setup_hidden_services(servicelines)
                continue

            # there's a whole bunch of FooPortLines (where "Foo" is
            # "Socks", "Control", etc) and some have defaults, some
            # don't but they all have FooPortLines, FooPort, and
            # __FooPort definitions so we only "do stuff" for the
            # "FooPortLines"
            if name.endswith('PortLines'):
                rn = self._find_real_name(name[:-5])
                self.parsers[rn] = String()  # not Port() because options etc
                self.list_parsers.add(rn)
                v = yield self.protocol.get_conf(name[:-5])
                v = v[name[:-5]]

                initial = []
                if v == DEFAULT_VALUE or v == 'auto':
                    try:
                        initial = defaults[name[:-5]]
                    except KeyError:
                        default_key = '__{}'.format(name[:-5])
                        default = yield self.protocol.get_conf_single(default_key)
                        if not default:
                            initial = []
                        else:
                            initial = [default]
                else:
                    initial = [self.parsers[rn].parse(v)]
                self.config[rn] = _ListWrapper(
                    initial, functools.partial(self.mark_unsaved, rn))

            # XXX for Virtual check that it's one of the *Ports things
            # (because if not it should be an error)
            if value in ('Dependant', 'Dependent', 'Virtual'):
                continue

            # there's a thing called "Boolean+Auto" which is -1 for
            # auto, 0 for false and 1 for true. could be nicer if it
            # was called AutoBoolean or something, but...
            value = value.replace('+', '_')

            inst = None
            # FIXME: put parser classes in dict instead?
            for cls in config_types:
                if cls.__name__ == value:
                    inst = cls()
            if not inst:
                raise RuntimeError("Don't have a parser for: " + value)
            v = yield self.protocol.get_conf(name)
            v = v[name]

            rn = self._find_real_name(name)
            self.parsers[rn] = inst
            if is_list_config_type(inst.__class__):
                self.list_parsers.add(rn)
                parsed = self.parsers[rn].parse(v)
                if parsed == [DEFAULT_VALUE]:
                    parsed = defaults.get(rn, [])
                self.config[rn] = _ListWrapper(
                    parsed, functools.partial(self.mark_unsaved, rn))

            else:
                if v == '' or v == DEFAULT_VALUE:
                    parsed = self.parsers[rn].parse(defaults.get(rn, DEFAULT_VALUE))
                else:
                    parsed = self.parsers[rn].parse(v)
                self.config[rn] = parsed

        # get any ephemeral services we own, or detached services.
        # these are *not* _ListWrappers because we don't care if they
        # change, nothing in Tor's config exists for these (probably
        # begging the question: why are we putting them in here at all
        # then...?)
        try:
            ephemeral = yield self.protocol.get_info('onions/current')
        except Exception as e:
            self.config['EphemeralOnionServices'] = []
        else:
            onions = []
            for line in ephemeral['onions/current'].split('\n'):
                onion = line.strip()
                if onion:
                    onions.append(
                        EphemeralOnionService(
                            self,
                            ports=[],  # no way to discover ports=
                            hostname=onion,
                            private_key=DISCARD,  # we don't know it, anyway
                            version=2,
                            detach=False,
                        )
                    )
            self.config['EphemeralOnionServices'] = onions

        try:
            detached = yield self.protocol.get_info('onions/detached')
        except Exception:
            self.config['DetachedOnionServices'] = []
        else:
            onions = []
            for line in detached['onions/detached'].split('\n'):
                onion = line.strip()
                if onion:
                    onions.append(
                        EphemeralOnionService(
                            self,
                            ports=[],  # no way to discover original ports=
                            hostname=onion,
                            detach=True,
                            private_key=DISCARD,
                        )
                    )
            self.config['DetachedOnionServices'] = onions
        defer.returnValue(self)

    def _setup_hidden_services(self, servicelines):

        def maybe_add_hidden_service():
            if directory is not None:
                if directory not in directories:
                    directories.append(directory)
                    if not auth:
                        service = FilesystemOnionService(
                            self, directory, ports, ver, group_read
                        )
                        hs.append(service)
                    else:
                        auth_type, clients = auth.split(' ', 1)
                        clients = clients.split(',')
                        if auth_type == 'basic':
                            auth0 = AuthBasic(clients)
                        elif auth_type == 'stealth':
                            auth0 = AuthStealth(clients)
                        else:
                            raise ValueError(
                                "Unknown auth type '{}'".format(auth_type)
                            )
                        parent_service = FilesystemAuthenticatedOnionService(
                            self, directory, ports, auth0, ver, group_read
                        )
                        for client_name in parent_service.client_names():
                            hs.append(parent_service.get_client(client_name))
                else:
                    raise RuntimeError("Trying to add hidden service with same HiddenServiceDir: %s" % directory)

        hs = []
        directory = None
        directories = []
        ports = []
        ver = None
        group_read = None
        auth = None
        for line in servicelines.split('\n'):
            if not len(line.strip()):
                continue

            if line == 'HiddenServiceOptions':
                continue
            k, v = line.split('=')
            if k == 'HiddenServiceDir':
                maybe_add_hidden_service()
                directory = v
                _directory = directory
                directory = os.path.abspath(directory)
                if directory != _directory:
                    warnings.warn(
                        "Directory path: %s changed to absolute path: %s" % (_directory, directory),
                        RuntimeWarning
                    )
                ports = []
                ver = None
                auth = None
                group_read = 0

            elif k == 'HiddenServicePort':
                ports.append(v)

            elif k == 'HiddenServiceVersion':
                ver = int(v)

            elif k == 'HiddenServiceAuthorizeClient':
                if auth is not None:
                    # definitely error, or keep going?
                    raise ValueError("Multiple HiddenServiceAuthorizeClient lines for one service")
                auth = v

            elif k == 'HiddenServiceDirGroupReadable':
                group_read = int(v)

            else:
                raise RuntimeError("Can't parse HiddenServiceOptions: " + k)

        maybe_add_hidden_service()

        name = 'HiddenServices'
        self.config[name] = _ListWrapper(
            hs, functools.partial(self.mark_unsaved, name))

    def config_args(self):
        '''
        Returns an iterator of 2-tuples (config_name, value), one for each
        configuration option in this config. This is more-or-less an
        internal method, but see, e.g., launch_tor()'s implementation
        if you think you need to use this for something.

        See :meth:`txtorcon.TorConfig.create_torrc` which returns a
        string which is also a valid ``torrc`` file
        '''

        everything = dict()
        everything.update(self.config)
        everything.update(self.unsaved)

        for (k, v) in list(everything.items()):
            if type(v) is _ListWrapper:
                if k.lower() == 'hiddenservices':
                    for x in v:
                        for (kk, vv) in x.config_attributes():
                            yield (str(kk), str(vv))

                else:
                    # FIXME actually, is this right? don't we want ALL
                    # the values in one string?!
                    for x in v:
                        yield (str(k), str(x))

            else:
                yield (str(k), str(v))

    def create_torrc(self):
        rtn = StringIO()

        for (k, v) in self.config_args():
            rtn.write(u'%s %s\n' % (k, v))

        return rtn.getvalue()
