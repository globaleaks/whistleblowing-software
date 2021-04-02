# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import os
import shutil
import weakref
import tempfile
import functools
from binascii import b2a_base64

from txtorcon.util import available_tcp_port
from txtorcon.socks import TorSocksEndpoint

from twisted.internet.interfaces import IStreamClientEndpointStringParserWithReactor
from twisted.internet import defer, error
from twisted.python import log
from twisted.python.deprecate import deprecated
from twisted.python.failure import Failure
from twisted.internet.interfaces import IStreamServerEndpointStringParser
from twisted.internet.interfaces import IStreamServerEndpoint
from twisted.internet.interfaces import IStreamClientEndpoint
from twisted.internet.interfaces import IListeningPort
from twisted.internet.interfaces import IAddress
from twisted.internet.endpoints import serverFromString
from twisted.internet.endpoints import clientFromString
from twisted.internet.endpoints import TCP4ClientEndpoint
# from twisted.internet.endpoints import UNIXClientEndpoint
# from twisted.internet import error
from twisted.plugin import IPlugin
from twisted.python.util import FancyEqMixin

from zope.interface import implementer
from zope.interface import Interface, Attribute

from .torconfig import TorConfig
from .onion import IAuthenticatedOnionClients
from .onion import FilesystemOnionService
from .onion import IFilesystemOnionService
from .onion import EphemeralOnionService
from .onion import FilesystemAuthenticatedOnionService
from .onion import EphemeralAuthenticatedOnionService
from .onion import AuthStealth  # , AuthBasic
from .torconfig import _endpoint_from_socksport_line
from .util import SingleObserver, _Version


_global_tor = None
_global_tor_lock = defer.DeferredLock()
# we need the lock because we (potentially) yield several times while
# "creating" the TorConfig instance


# in an ideal world, we'd have "get_global_tor()" and it would return
# a Tor instance, and all would be well. HOWEVER, "get_global_tor" was
# previously released to return a TorConfig instance. So it still
# needs to do that, *and* it should be the very same TorConfig
# instance attached to the "global Tor instance".
# Anyway: get_global_tor_instance() is the newst API, and the one new
# code should use (if at all -- ideally just use a .global_tor()
# factory-function call instead)

@defer.inlineCallbacks
def get_global_tor_instance(reactor,
                            control_port=None,
                            progress_updates=None,
                            _tor_launcher=None):
    """
    Normal users shouldn't need to call this; use
    TCPHiddenServiceEndpoint::system_tor instead.

    :return Tor: a 'global to this Python process' instance of
        Tor. There isn't one of these until the first time this method
        is called. All calls to this method return the same instance.
    """
    global _global_tor
    global _global_tor_lock
    yield _global_tor_lock.acquire()

    if _tor_launcher is None:
        # XXX :( mutual dependencies...really get_global_tor_instance
        # should be in controller.py if it's going to return a Tor
        # instance.
        from .controller import launch
        _tor_launcher = launch

    try:
        if _global_tor is None:
            _global_tor = yield _tor_launcher(reactor, progress_updates=progress_updates)

        else:
            config = yield _global_tor.get_config()
            already_port = config.ControlPort
            if control_port is not None and control_port != already_port:
                raise RuntimeError(
                    "ControlPort is already '{}', but you wanted '{}'",
                    already_port,
                    control_port,
                )

        defer.returnValue(_global_tor)
    finally:
        _global_tor_lock.release()


@deprecated(_Version("txtorcon", 18, 0, 0))
@defer.inlineCallbacks
def get_global_tor(reactor, control_port=None,
                   progress_updates=None,
                   _tor_launcher=None):
    """
    See description of :class:`txtorcon.TCPHiddenServiceEndpoint`'s
    class-method ``global_tor``

    :param control_port:
        a TCP port upon which to run the launched Tor's
        control-protocol (selected by the OS by default).

    :param progress_updates:
        A callable that takes 3 args: ``percent, tag, message`` which
        is called when Tor announcing some progress setting itself up.

    :returns:
        a ``Deferred`` that fires a :class:`txtorcon.TorConfig` which is
        bootstrapped.

    The _tor_launcher keyword arg is internal-only.
    """
    tor = yield get_global_tor_instance(
        reactor,
        control_port=control_port,
        progress_updates=progress_updates,
        _tor_launcher=_tor_launcher,
    )
    cfg = yield tor.get_config()
    defer.returnValue(cfg)


class IProgressProvider(Interface):
    """FIXME move elsewhere? think harder?"""
    def add_progress_listener(listener):
        """
        Adds a progress listener. The listener is a callable that gets
        called with 3 arguments corresponding to Tor's updates:
        (percent, tag, message). percent is an integer from 0 to 100,
        tag and message are both strings. (message is the
        human-readable one)
        """


# XXX essentially, we either want an ephemeral vs. non-ephemeral etc
# endpoint instance, *or* we just make this a "delayed" version of
# create_onion_service -- i.e. holds all the same args as that and
# listen() instantiates it and knows "which" tor it wants.
@implementer(IStreamServerEndpoint)
@implementer(IProgressProvider)
class TCPHiddenServiceEndpoint(object):
    """
    This represents something listening on an arbitrary local port
    that has a Tor configured with a Hidden Service pointing at
    it. :api:`twisted.internet.endpoints.TCP4ServerEndpoint
    <TCP4ServerEndpoint>` is used under the hood to do the local
    listening.

    There are three main ways to use this class, and you are
    encouraged to use the @classmethod ways of creating instances:
    `system_tor <#txtorcon.TCPHiddenServiceEndpoint.system_tor>`_,
    `global_tor <#txtorcon.TCPHiddenServiceEndpoint.global_tor>`_,
    and `private_tor <#txtorcon.TCPHiddenServiceEndpoint.private_tor>`_

    1. system_tor(...) connects to an already-started tor on the
       endpoint you specify; stricly speaking not a "system" tor since
       you could have spawned it some other way. See `Tor bug 11291
       <https://trac.torproject.org/projects/tor/ticket/11291>`_
       however.

    2. global_tor(...) refers to a single possible Tor instance
       per python process. So the first call to this launches a new Tor, and
       subsequent calls re-use the existing Tor (that is, add more hidden
       services to it).

    3. private_tor(...) launches a new Tor instance no matter what, so
       it will have just the one hidden serivce on it.

    If you need to set configuration options that are not reflected in
    any of the method signatures above, you'll have to construct an
    instance of this class yourself (i.e. with a TorConfig instance
    you've created).

    No matter how you came by this endpoint instance, you should call
    `listen()` on it to trigger any work required to create the
    service: Tor will be launched or connected-to; config for the
    onion service will be added; the uploading of descriptors is
    awaited.

    The ``Deferred`` from ``listen()`` will fire with an
    ``IListeningPort`` whose ``getHost()`` will return a
    :class:`txtorcon.TorOnionAddress`. The port object also has a
    `.onion_service` property which resolves to the
    :class:`txtorcon.IOnionService` or
    :class:`txtorcon.IAuthenticatedOnionClients` instance (and from
    which you can recover private keys, the hostname, etc)

    :ivar onion_uri: the public key, like ``timaq4ygg2iegci7.onion``
        which came from the hidden_service_dir's ``hostname`` file

    :ivar onion_private_key: the contents of ``hidden_service_dir/private_key``

    :ivar hidden_service_dir: the data directory, either passed in or created
        with ``tempfile.mkdtemp``

    **NOTE** that if you do not specify a `version=` then you will get
    a version 2 service (new onion APIs return version=3 services by
    default). This is for backwards-compatiblity reasons, as version=
    didn't exist before 18.0.0
    """

    @classmethod
    def system_tor(cls, reactor, control_endpoint, public_port,
                   hidden_service_dir=None,
                   local_port=None,
                   ephemeral=None,
                   auth=None,
                   private_key=None,
                   version=None,
                   single_hop=None):
        """
        This returns a TCPHiddenServiceEndpoint connected to the
        endpoint you specify in `control_endpoint`. After connecting, a
        single hidden service is added. The endpoint can be a Unix
        socket if Tor's `ControlSocket` option was used (instead of
        `ControlPort`).

        .. note::

            If Tor bug #11291 is not yet fixed, this won't work if you
            only have Group access. XXX FIXME re-test
        """

        from txtorcon.controller import connect
        tor = connect(reactor, control_endpoint)
        tor.addCallback(lambda t: t.get_config())
        # tor is a Deferred
        return TCPHiddenServiceEndpoint(
            reactor, tor, public_port,
            hidden_service_dir=hidden_service_dir,
            local_port=local_port,
            ephemeral=ephemeral,
            private_key=private_key,
            auth=auth,
            version=version,
            single_hop=single_hop,
        )

    @classmethod
    def global_tor(cls, reactor, public_port,
                   hidden_service_dir=None,
                   local_port=None,
                   control_port=None,
                   stealth_auth=None,  # backwards-compat; don't use
                   auth=None,
                   ephemeral=None,
                   private_key=None,
                   version=None,
                   single_hop=None):
        """
        This returns a TCPHiddenServiceEndpoint connected to a
        txtorcon global Tor instance. The first time you call this, a
        new Tor will be launched. Subsequent calls will re-use the
        same connection (in fact, the very same TorControlProtocol and
        TorConfig instances). If the options you pass are incompatible
        with an already-launched Tor, RuntimeError will be thrown.

        It's probably best to not specify any option besides
        `public_port`, `hidden_service_dir`, and maybe `local_port`
        unless you have a specific need to.

        You can also access this global txtorcon instance via
        :meth:`txtorcon.get_global_tor_instance` (which is precisely what
        this method uses to get it).

        All keyword options have defaults (e.g. random ports, or
        tempdirs).

        :param stealth_auth: **Deprecated**
            None, or a list of strings -- one for each stealth
            authenticator you require. Use `auth=` now.

        :param auth: None or an :class:`txtorcon.AuthBasic` or
            :class:`txtorcon.AuthStealth` instance
        """

        def progress(*args):
            progress.target(*args)
        tor = get_global_tor_instance(
            reactor,
            control_port=control_port,
            progress_updates=progress
        )
        # tor is a Deferred here, but endpoint resolves it in the
        # listen() call. Also, we want it to resolve to a TorConfig,
        # not a Tor
        tor.addCallback(lambda tor: tor.get_config())
        r = TCPHiddenServiceEndpoint(
            reactor, tor, public_port,
            hidden_service_dir=hidden_service_dir,
            local_port=local_port,
            auth=auth,
            ephemeral=ephemeral,
            private_key=private_key,
            version=version,
            single_hop=single_hop,
        )
        progress.target = r._tor_progress_update
        return r

    @classmethod
    def private_tor(cls, reactor, public_port,
                    hidden_service_dir=None,
                    local_port=None,
                    control_port=None,
                    ephemeral=None,
                    private_key=None,
                    auth=None,
                    version=None,
                    single_hop=None):
        """
        This returns a TCPHiddenServiceEndpoint that's always
        connected to its own freshly-launched Tor instance. All
        keyword options have defaults (e.g. random ports, or
        tempdirs).
        """

        def progress(*args):
            progress.target(*args)

        from .controller import launch
        tor = launch(
            reactor,
            progress_updates=progress,
            control_port=control_port,
        )
        tor.addCallback(lambda t: t.get_config())
        r = TCPHiddenServiceEndpoint(
            reactor, tor, public_port,
            hidden_service_dir=hidden_service_dir,
            local_port=local_port,
            ephemeral=ephemeral,
            private_key=private_key,
            auth=auth,
            version=version,
            single_hop=single_hop,
        )
        progress.target = r._tor_progress_update
        return r

    def __init__(self, reactor, config, public_port,
                 hidden_service_dir=None,
                 local_port=None,
                 auth=None,  # new way to pass authentication information
                 stealth_auth=None,  # deprecated; use auth=
                 ephemeral=None,  # will be set to True, unless hsdir spec'd
                 private_key=None,
                 group_readable=False,
                 version=None,
                 single_hop=None):
        """
        :param reactor:
            :api:`twisted.internet.interfaces.IReactorTCP` provider

        :param config:
            :class:`txtorcon.TorConfig` instance or a Deferred yielding one

        :param public_port:
            The port number we will advertise in the hidden serivces
            directory.

        :param local_port:
            The port number we will perform our local tcp listen on and
            receive incoming connections from the tor process.

        :param hidden_service_dir:
            If not None, point to a HiddenServiceDir directory
            (i.e. with "hostname" and "private_key" files in it). If
            not provided, one is created with temp.mkdtemp() AND
            DELETED when the reactor shuts down.

        :param auth:
            An AuthBasic or AuthStealth instance (or None)

        :param stealth_auth:
            **Deprecated; use ``auth=``**. This is for backwards-comapatibility only.

        :param endpoint_generator:
            A callable that generates a new instance of something that
            implements IServerEndpoint (by default TCP4ServerEndpoint)

        :param group_readable:
            Only for filesystem services. Causes the directory to be
            group-readable when Tor creates it.

        :param version:
            Either None, 2 or 3 to specify a version 2 service or
            Proposition 224 (version 3) service.

        :param single_hop: if True, pass the `NonAnonymous` flag. Note
            that Tor options `HiddenServiceSingleHopMode`,
            `HiddenServiceNonAnonymousMode` must be set to `1` and there
            must be no `SOCKSPort` configured for this to actually work.
        """

        # this supports API backwards-compatibility -- if you didn't
        # explicitly specify ephemeral=True, but *did* set
        # hidden_service_dir
        if ephemeral is None:
            ephemeral = True
            if hidden_service_dir is not None:
                ephemeral = False

        # backwards-compatibility for stealth_auth= kwarg
        if stealth_auth is not None:
            log.msg("'stealth_auth' is deprecated; use auth= instead")
            if auth is not None:
                raise ValueError(
                    "Both stealth_auth= and auth= passed; use auth= only for new code"
                )
            auth = AuthStealth(stealth_auth)
            stealth_auth = None

        if ephemeral and isinstance(auth, AuthStealth):
            raise ValueError(
                "'ephemeral=True' onion services don't support 'stealth' auth"
            )

        if ephemeral and hidden_service_dir is not None:
            raise ValueError(
                "Specifying 'hidden_service_dir' is incompatible"
                " with 'ephemeral=True'"
            )

        if private_key is not None and not ephemeral:
            raise ValueError(
                "'private_key' only understood for ephemeral services"
            )

        if single_hop and not ephemeral:
            raise ValueError(
                "'single_hop=' flag only makes sense for ephemeral onions"
            )

        self._reactor = reactor
        self._config = defer.maybeDeferred(lambda: config)
        self.public_port = public_port
        self.local_port = local_port
        self.auth = auth

        self.ephemeral = ephemeral
        self.private_key = private_key
        # if we're an ephemeral service, hidden_service_dir is None
        # and ephemeral is True
        self.hidden_service_dir = hidden_service_dir
        self.tcp_listening_port = None
        self.hiddenservice = None
        self.group_readable = group_readable
        self.version = version
        self.single_hop = single_hop
        self.retries = 0

        if self.version is None:
            self.version = 2

        '''for IProgressProvider to add_progress_listener'''
        self.progress_listeners = []

        if not self.ephemeral:
            if self.hidden_service_dir is None:
                self.hidden_service_dir = tempfile.mkdtemp(prefix='tortmp')
                log.msg('Will delete "%s" at shutdown.' % self.hidden_service_dir)
                delete = functools.partial(shutil.rmtree, self.hidden_service_dir)
                self._reactor.addSystemEventTrigger('before', 'shutdown', delete)

    @property
    def onion_uri(self):
        if self.hiddenservice is None:
            return None
        if IAuthenticatedOnionClients.providedBy(self.hiddenservice):
            return _maybe_unique_host(self.hiddenservice)
        return self.hiddenservice.hostname

    @property
    def onion_private_key(self):
        if self.hiddenservice is None:
            return None
        return self.hiddenservice.private_key

    def add_progress_listener(self, listener):
        """IProgressProvider API"""
        self.progress_listeners.append(listener)

    def _descriptor_progress_update(self, prog, tag, summary):
        # 'prog' here ranges from 0 -> 100.0 but we've only reserved
        # "10.0" of the range for the "upload descriptors" portion,
        # and we know that Tor has launched, so we're mapping "prog"
        # to the "100 -> 110" part of the range
        scaled_prog = (100.0 + (prog / 10.0)) * (100.0 / 110.0)
        for p in self.progress_listeners:
            try:
                p(scaled_prog, tag, summary)
            except Exception:
                log.err()

    def _tor_progress_update(self, prog, tag, summary):
        # we re-adjust the percentage-scale, using 105% and 110% for
        # the two parts of waiting for descriptor upload. That is, we
        # want: 110 * constant == 100.0
        scaled_prog = prog * (100.0 / 110.0)
        log.msg('%d%% %s' % (scaled_prog, summary))
        for p in self.progress_listeners:
            try:
                p(scaled_prog, tag, summary)
            except Exception:
                log.err()

    @defer.inlineCallbacks
    def listen(self, protocolfactory):
        """
        Implement :api:`twisted.internet.interfaces.IStreamServerEndpoint
        <IStreamServerEndpoint>`.

        Returns a Deferred that delivers an
        :api:`twisted.internet.interfaces.IListeningPort` implementation.

        This object will also have a `.onion_service` property which
        resolve to an instance implementing
        :class:`txtorcon.IOnionService` or
        :class:`txtorcon.IAuthenticatedOnionClients` (depending on
        whether the service is authenticated or not).

        At this point, Tor will have fully started up and successfully
        accepted the hidden service's config. The Onion Service's
        descriptor will be uploaded to at least one directory (as
        reported via the `HS_DESC` event).
        """

        self.protocolfactory = protocolfactory

        # self._config is always a Deferred; see __init__
        self._config = yield self._config
        if not isinstance(self._config, TorConfig):
            raise ValueError(
                'Expected a TorConfig instance but '
                'got "{}.{}" instead.'.format(
                    self._config.__class__.__module__,
                    self._config.__class__.__name__,
                )
            )
        # just to be sure:
        yield self._config.post_bootstrap

        # XXX - perhaps allow the user to pass in an endpoint
        # descriptor and make this one the default? Then would
        # probably want to check for "is a local interface or not" and
        # at *least* warn if it's not local...
        self.tcp_endpoint = serverFromString(
            self._reactor,
            'tcp:0:interface=127.0.0.1',
        )
        d = self.tcp_endpoint.listen(self.protocolfactory)
        self.tcp_listening_port = yield d
        self.local_port = self.tcp_listening_port.getHost().port

        # XXX can we detect if tor supports Unix sockets here? I guess
        # we could try "unix:/tmp/blarg", and if it fails, try
        # "tcp:0:interface=127.0.0.1" ...?

        # specifically NOT creating the hidden-service dir; letting
        # Tor do it will more-likely result in a usable situation...
        if not self.ephemeral:
            if not os.path.exists(self.hidden_service_dir):
                log.msg(
                    'Noting that "%s" does not exist; letting Tor create it.' %
                    self.hidden_service_dir
                )

        # see note in _tor_progress_update; we extend the percent
        # range to 110% for the descriptor upload
        self._descriptor_progress_update(
            0.0, 'wait_descriptor', 'uploading descriptor'
        )

        # see if the hidden-serivce instance we want is already in the
        # config; for non-ephemeral services, the directory is unique;
        # for ephemeral services, the key should exist and be unique.
        already = False
        if self.ephemeral:
            already = self.hiddenservice is not None
        else:
            hs_dirs = [hs.dir for hs in self._config.HiddenServices if hasattr(hs, 'dir')]
            already = os.path.abspath(self.hidden_service_dir) in hs_dirs

        if not already:
            if self.ephemeral:
                if self.auth is not None:
                    create_d = EphemeralAuthenticatedOnionService.create(
                        self._reactor,
                        self._config,
                        ['%d 127.0.0.1:%d' % (self.public_port, self.local_port)],
                        private_key=self.private_key,
                        detach=False,
                        progress=self._descriptor_progress_update,
                        version=self.version,
                        auth=self.auth,
                        single_hop=self.single_hop,
                    )

                else:
                    create_d = EphemeralOnionService.create(
                        self._reactor,
                        self._config,
                        ['%d 127.0.0.1:%d' % (self.public_port, self.local_port)],
                        private_key=self.private_key,
                        detach=False,
                        progress=self._descriptor_progress_update,
                        version=self.version,
                        single_hop=self.single_hop,
                    )
            else:
                if self.auth is not None:
                    create_d = FilesystemAuthenticatedOnionService.create(
                        self._reactor,
                        self._config,
                        self.hidden_service_dir,
                        ['%d 127.0.0.1:%d' % (self.public_port, self.local_port)],
                        auth=self.auth,  # AuthBasic or AuthStealth
                        progress=self._descriptor_progress_update,
                        group_readable=self.group_readable,
                        version=self.version,
                    )
                else:
                    create_d = FilesystemOnionService.create(
                        self._reactor,
                        self._config,
                        self.hidden_service_dir,
                        ['%d 127.0.0.1:%d' % (self.public_port, self.local_port)],
                        progress=self._descriptor_progress_update,
                        group_readable=self.group_readable,
                        version=self.version,
                    )
            self.hiddenservice = yield create_d

        else:
            if not self.ephemeral:
                for hs in self._config.HiddenServices:
                    if hs.dir == os.path.abspath(self.hidden_service_dir):
                        self.hiddenservice = hs

        assert self.hiddenservice is not None, "internal error"

        if IAuthenticatedOnionClients.providedBy(self.hiddenservice):
            log.msg('Started authenticated onion service on:')
            for nm in self.hiddenservice.client_names():
                log.msg('  {}: {}'.format(nm, self.hiddenservice.get_client(nm).hostname))
        else:
            log.msg('Started onion service on %s:%d' % (self.onion_uri, self.public_port))

        # XXX should just return self.hiddenservice here??
        # -> no, don't think so for a couple reasons:

        # 1. it's "ports" in the services, so "TorOnionListeningPort"
        # is the only thing that knows there's just one in this one
        # (so can provide .local_port -> shoujld be local_endpoint I
        # guess actually...)
        # 2. anyway, can provide access to the "real" hs anyway if we want
        defer.returnValue(
            TorOnionListeningPort(
                self.tcp_listening_port,
                self.public_port,
                self.hiddenservice,
                self._config,
            )
        )


@implementer(IAddress)
class TorOnionAddress(FancyEqMixin, object):
    """
    A ``TorOnionAddress`` represents the public address of a Tor onion
    service. Instances of these come from calling the Twisted method
    `.getHost()` on :api:`twisted.internet.interfaces.IListeningPort`
    which was returned from the :class:`txtorcon.TCPHiddenServiceEndpoint.listen`

    :ivar type: A string describing the type of transport, 'onion'.

    :ivar onion_port: The public port we're advertising

    :ivar onion_key: the private key for the service
    """
    compareAttributes = ('type', 'onion_port', 'onion_key')
    type = 'onion'

    # for authenticated services, there is a private-key for "the
    # service"; for stealth-auth'd services, there are *also*
    # private-keys for each client

    def __init__(self, port, hs):
        self.onion_port = port

        # this gets a bit weird .. partially for backwards-
        # compatibility: .onion_uri is/was an existing property -- but
        # doesn't always make sense. so, users should be encouraged to
        # use .onion_service and access things directly (i.e. they
        # know if they have an authenticated service or not, or can
        # find out via .providedBy())

        if IAuthenticatedOnionClients.providedBy(hs):
            try:
                self.onion_uri = _maybe_unique_host(hs)
            except ValueError:
                self.onion_uri = None
        else:
            self.onion_uri = hs.hostname
        self._hiddenservice = hs

    @property
    def onion_service(self):
        return self._hiddenservice

    @property
    def onion_key(self):
        return self._hiddenservice.private_key

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.onion_uri)

    def __hash__(self):
        # should be "URIs", not URI
        return hash((self.type, self.onion_uri, self.onion_port))


class IHiddenService(Interface):
    local_address = Attribute(
        'The actual machine address we are listening on.')
    hidden_service_dir = Attribute(
        'The hidden service directory, where "hostname" and "private_key" '
        'files live.')
    tor_config = Attribute(
        'The TorConfig object attached to the Tor hosting this hidden service '
        '(in turn has .protocol for TorControlProtocol).')


@implementer(IListeningPort)
@implementer(IHiddenService)  # deprecated; use .onion_service
class TorOnionListeningPort(object):
    """
    Our TCPHiddenServiceEndpoint's `listen` method will return a deferred
    which fires an instance of this object.
    The `getHost` method will return a TorOnionAddress instance... which
    can be used to determine the onion address of a newly created Tor Hidden
    Service.

    `startListening` and `stopListening` methods proxy to the "TCP
    ListeningPort" object...
    which implements IListeningPort interface but has many more
    responsibilities we needn't worry about here.
    """

    def __init__(self, listening_port, public_port, hiddenservice, tor_config):
        # XXX can get these from the service
        self._local_address = listening_port
        self.public_port = public_port
        # XXX should this be a weakref too? is there circ-ref here?
        self._service = hiddenservice
        # XXX why is this a weakref? circ-ref? (also, can get from the service anyway, no?)
        self._config_ref = weakref.ref(tor_config)
        self._address = TorOnionAddress(public_port, hiddenservice)

    def startListening(self):
        """IListeningPort API"""
        self._local_address.startListening()

    def stopListening(self):
        """IListeningPort API"""
        self._local_address.stopListening()

    def getHost(self):
        """IListeningPort API"""
        return self._address

    def __str__(self):
        return '<TorOnionListeningPort %s:%d>' % (self._address.onion_uri, self._address.onion_port)

    # preferred method of accessing everything
    @property
    def onion_service(self):
        return self._service

    # these are implemented by the now-deprecated IHiddenService API;
    # do not use for new code -- get all information from .onion_service

    @property
    @deprecated(_Version("txtorcon", 18, 0, 0))
    def tor_config(self):
        return self._config_ref()  # None if ref dead

    @property
    @deprecated(_Version("txtorcon", 18, 0, 0))
    def local_address(self):
        return self._local_address

    @property
    @deprecated(_Version("txtorcon", 18, 0, 0))
    def hidden_service_dir(self):
        if not IFilesystemOnionService.providedBy(self._service):
            raise ValueError(
                "No 'hidden_service_dir' because our _service doesn't provide"
                " IFilesystemOnionService"
            )
        return self._service.directory


def _load_private_key_file(fname):
    """
    Loads an onion-service private-key from the given file. This can
    be either a 'key blog' as returned from a previous ADD_ONION call,
    or a v3 or v2 file as created by Tor when using the
    HiddenServiceDir directive.

    In any case, a key-blob suitable for ADD_ONION use is returned.
    """
    with open(fname, "rb") as f:
        data = f.read()
    if b"\x00\x00\x00" in data:  # v3 private key file
        blob = data[data.find(b"\x00\x00\x00") + 3:]
        return u"ED25519-V3:{}".format(b2a_base64(blob.strip()).decode('ascii').strip())
    if b"-----BEGIN RSA PRIVATE KEY-----" in data:  # v2 RSA key
        blob = "".join(data.decode('ascii').split('\n')[1:-2])
        return u"RSA1024:{}".format(blob)
    blob = data.decode('ascii').strip()
    if ':' in blob:
        kind, key = blob.split(':', 1)
        if kind in ['ED25519-V3', 'RSA1024']:
            return blob
    raise ValueError(
        "'{}' does not appear to contain v2 or v3 private key data".format(
            fname,
        )
    )


@implementer(IStreamServerEndpointStringParser, IPlugin)
class TCPHiddenServiceEndpointParser(object):
    """
    This provides a twisted IPlugin and
    IStreamServerEndpointsStringParser so you can call
    :api:`twisted.internet.endpoints.serverFromString
    <serverFromString>` with a string argument like:

    ``onion:80:localPort=9876:controlPort=9052:hiddenServiceDir=/dev/shm/foo``

    ...or simply:

    ``onion:80``

    If ``controlPort`` is specified, it means connect to an already-running Tor
    on that port and add a hidden-serivce to it.

    ``localPort`` is optional and if not specified, a port is selected by
    the OS.

    If ``hiddenServiceDir`` is not specified, one is created with
    ``tempfile.mkdtemp()``. The IStreamServerEndpoint returned will be
    an instance of :class:`txtorcon.TCPHiddenServiceEndpoint`

    If ``privateKey`` or ``privateKeyFile`` is specified, the service
    will be "ephemeral" and Tor will receive the private key via the
    ADD_ONION control-port command.
    """
    prefix = "onion"

    # note that these are all camelCase because Twisted uses them to
    # do magic parsing stuff, and to conform to Twisted's conventions
    # we should use camelCase in the endpoint definitions...

    def parseStreamServer(self, reactor, public_port, localPort=None,
                          controlPort=None, hiddenServiceDir=None,
                          privateKey=None, privateKeyFile=None,
                          version=None, singleHop=None):
        """
        :api:`twisted.internet.interfaces.IStreamServerEndpointStringParser`
        """

        if privateKeyFile is not None:
            if privateKey is not None:
                raise ValueError(
                    "Can't specify both privateKey= and privateKeyFile="
                )
            privateKey = _load_private_key_file(privateKeyFile)
            privateKeyFile = None

        if hiddenServiceDir is not None and privateKey is not None:
            raise ValueError(
                "Only one of hiddenServiceDir and privateKey/privateKeyFile accepted"
            )

        if singleHop is not None:
            if singleHop.strip().lower() in ['0', 'false']:
                singleHop = False
            elif singleHop.strip().lower() in ['1', 'true']:
                singleHop = True
            else:
                raise ValueError(
                    "singleHop= param must be 'true' or 'false'"
                )
        else:
            singleHop = False

        if version is not None:
            try:
                version = int(version)
            except ValueError:
                raise ValueError(
                    "version must be an integer"
                )
        if version not in (None, 2, 3):
            raise ValueError(
                "Invalid version '{}'".format(version)
            )

        ephemeral = None

        public_port = int(public_port)

        if localPort is not None:
            localPort = int(localPort)

        hsd = hiddenServiceDir
        if hsd:
            orig = hsd
            hsd = os.path.expanduser(hsd)
            hsd = os.path.realpath(hsd)
            if orig != hsd:
                log.msg('Using "%s" for hsd' % hsd)

        if controlPort:
            try:
                ep = clientFromString(
                    reactor, "tcp:host=127.0.0.1:port=%d" % int(controlPort))
            except ValueError:
                ep = clientFromString(reactor, "unix:path=%s" % controlPort)
            return TCPHiddenServiceEndpoint.system_tor(
                reactor, ep, public_port,
                hidden_service_dir=hsd,
                local_port=localPort,
                ephemeral=ephemeral,
                version=version,
                private_key=privateKey,
                single_hop=singleHop,
            )

        return TCPHiddenServiceEndpoint.global_tor(
            reactor, public_port,
            hidden_service_dir=hsd,
            local_port=localPort,
            control_port=controlPort,
            ephemeral=ephemeral,
            version=version,
            private_key=privateKey,
            single_hop=singleHop,
        )


@defer.inlineCallbacks
def _create_socks_endpoint(reactor, control_protocol, socks_config=None):
    """
    Internal helper.

    This uses an already-configured SOCKS endpoint from the attached
    Tor, or creates a new TCP one (and configures Tor with it). If
    socks_config is non-None, it is a SOCKSPort line and will either
    be used if it already exists or will be created.
    """
    socks_ports = yield control_protocol.get_conf('SOCKSPort')
    if socks_ports:
        socks_ports = list(socks_ports.values())[0]
        if not isinstance(socks_ports, list):
            socks_ports = [socks_ports]
        # see TorConfig for more fun-times regarding *PortLines, including
        # the __*Port things...
        if socks_ports == ['DEFAULT']:
            default = yield control_protocol.get_conf_single('__SocksPort')
            socks_ports = [default]
    else:
        # return from get_conf was an empty dict; we want a list
        socks_ports = []

    # everything in the SocksPort list can include "options" after the
    # initial value. We don't care about those, but do need to strip
    # them.
    socks_ports = [port.split()[0] for port in socks_ports]

    # could check platform? but why would you have unix ports on a
    # platform that doesn't?
    unix_ports = set([p for p in socks_ports if p.startswith('unix:')])
    tcp_ports = set(socks_ports) - unix_ports

    socks_endpoint = None
    for p in list(unix_ports) + list(tcp_ports):  # prefer unix-ports
        if socks_config and p != socks_config:
            continue
        try:
            socks_endpoint = _endpoint_from_socksport_line(reactor, p)
        except Exception as e:
            log.err(
                Failure(),
                "failed to process SOCKS port '{}': {}".format(p, e)
            )

    # if we still don't have an endpoint, nothing worked (or there
    # were no SOCKSPort lines at all) so we add config to tor
    if socks_endpoint is None:
        if socks_config is None:
            # is a unix-socket in /tmp on a supported platform better than
            # this?
            port = yield available_tcp_port(reactor)
            socks_config = str(port)
        socks_ports.append(socks_config)

        # NOTE! We must set all the ports in one command or we'll
        # destroy pre-existing config
        args = []
        for p in socks_ports:
            args.append('SOCKSPort')
            args.append(p)
        yield control_protocol.set_conf(*args)
        socks_endpoint = _endpoint_from_socksport_line(reactor, socks_config)

    assert socks_endpoint is not None
    defer.returnValue(socks_endpoint)


@implementer(IStreamClientEndpoint)
class TorClientEndpoint(object):
    """
    An IStreamClientEndpoint which establishes a connection via Tor.

    You should not instantiate these directly; use
    ``clientFromString()``, :meth:`txtorcon.Tor.stream_via` or
    :meth:`txtorcon.Circuit.stream_via`

    :param host:
        The hostname to connect to. This of course can be a Tor Hidden
        Service onion address.

    :param port: The tcp port or Tor Hidden Service port.

    :param socks_endpoint: An IStreamClientEndpoint pointing at (one
        of) our Tor's SOCKS ports. These can be instantiated with
        :meth:`txtorcon.TorConfig.socks_endpoint`.

    :param tls: Can be False or True (to get default Browser-like
        hostname verification) or the result of calling
        optionsForClientTLS() yourself. Default is True.
    """

    socks_ports_to_try = [9050, 9150]

    @classmethod
    def from_connection(cls, reactor, control_protocol, host, port,
                        tls=None,
                        socks_endpoint=None):
        if socks_endpoint is None:
            socks_endpoint = _create_socks_endpoint(reactor, control_protocol)
        return TorClientEndpoint(
            host, port,
            socks_endpoint=socks_endpoint,
            tls=tls,
            reactor=reactor,
        )

    def __init__(self,
                 host, port,
                 socks_endpoint=None,  # can be Deferred
                 tls=False,

                 # XXX our custom SOCKS stuff doesn't support auth (yet?)
                 socks_username=None, socks_password=None,
                 reactor=None, **kw):
        if host is None or port is None:
            raise ValueError('host and port must be specified')

        self.host = host
        self.port = int(port)
        self._socks_endpoint = socks_endpoint
        self._socks_username = socks_username
        self._socks_password = socks_password
        self._tls = tls
        # XXX FIXME we 'should' probably include 'reactor' as the
        # first arg to this class, but technically that's a
        # breaking change :(
        self._reactor = reactor
        if reactor is None:
            from twisted.internet import reactor
            self._reactor = reactor

        # backwards-compatibility: you used to specify a TCP SOCKS
        # endpoint via socks_host= and socks_port= kwargs
        if self._socks_endpoint is None:
            try:
                self._socks_endpoint = TCP4ClientEndpoint(
                    reactor,
                    kw['socks_hostname'],
                    kw['socks_port'],
                )
                # XXX should deprecation-warn here
            except KeyError:
                pass

        # this is a separate "if" from above in case socks_endpoint
        # was None but the user specified the (old)
        # socks_hostname/socks_port (in which case we do NOT want
        # guessing_enabled
        if self._socks_endpoint is None:
            self._socks_guessing_enabled = True
        else:
            self._socks_guessing_enabled = False

        # XXX think, do we want to expose these like this? Or some
        # other way (because they're for stream-isolation, not actual
        # auth)
        self._socks_username = socks_username
        self._socks_password = socks_password
        self._when_address = SingleObserver()

    def _get_address(self):
        """
        internal helper.

        *le sigh*. This is basically just to support
        TorCircuitEndpoint; see TorSocksEndpoint._get_address(). There
        shouldn't be any need for "actual users" to need this!

        This returns a Deferred that fires once:
          - we have an underlying SOCKS5 endpoint
          - ...and it has received a local connection (and hence the address/port)
        """
        return self._when_address.when_fired()

    @defer.inlineCallbacks
    def connect(self, protocolfactory):
        last_error = None
        # XXX fix in socks.py stuff for socks_username, socks_password
        if self._socks_username or self._socks_password:
            raise RuntimeError(
                "txtorcon socks support doesn't yet do username/password"
            )
        if self._socks_endpoint is not None:
            socks_ep = TorSocksEndpoint(
                self._socks_endpoint,
                self.host, self.port,
                self._tls,
            )
            # forward the address to any listeners we have
            socks_ep._get_address().addCallback(self._when_address.fire)
            proto = yield socks_ep.connect(protocolfactory)
            defer.returnValue(proto)
        else:
            for socks_port in self.socks_ports_to_try:
                tor_ep = TCP4ClientEndpoint(
                    self._reactor,
                    "127.0.0.1",  # XXX socks_hostname, no?
                    socks_port,
                )
                socks_ep = TorSocksEndpoint(tor_ep, self.host, self.port, self._tls)
                # forward the address to any listeners we have
                socks_ep._get_address().addCallback(self._when_address.fire)
                try:
                    proto = yield socks_ep.connect(protocolfactory)
                    defer.returnValue(proto)

                except error.ConnectError as e0:
                    last_error = e0
            if last_error is not None:
                raise last_error


@implementer(IPlugin, IStreamClientEndpointStringParserWithReactor)
class TorClientEndpointStringParser(object):
    """
    This provides a twisted IPlugin and
    IStreamClientEndpointsStringParser so you can call
    :api:`twisted.internet.endpoints.clientFromString
    <clientFromString>` with a string argument like:

    ``tor:host=timaq4ygg2iegci7.onion:port=80:socksPort=9050``

    ...or simply:

    ``tor:host=timaq4ygg2iegci7.onion:port=80``

    You may also include a username + password. By default, Tor will
    not put two streams that provided different authentication on the
    same circuit.

    ``tor:host=torproject.org:port=443:socksUsername=foo:socksPassword=bar``

    If ``socksPort`` is specified, it means only use that port to
    attempt to proxy through Tor. If unspecified, we ... XXX?

    NOTE that I'm using camelCase variable names in the endpoint
    string to be consistent with the rest of Twisted's naming (and
    their endpoint parsers).

    XXX FIXME if there is no Tor instance found at socksPort, we
    should launch one. Perhaps a separate option? (Should be on by
    default, though, I think).
    """
    prefix = "tor"

    def _parseClient(self, reactor,
                     host=None, port=None,
                     socksHostname=None, socksPort=None,
                     socksUsername=None, socksPassword=None):
        if port is not None:
            port = int(port)

        ep = None
        if socksPort is not None:
            # Tor can speak SOCKS over unix, too, but this doesn't let
            # us pass one ...
            ep = TCP4ClientEndpoint(reactor, socksHostname, int(socksPort))
        return TorClientEndpoint(
            host, port,
            socks_endpoint=ep,
            socks_username=socksUsername,
            socks_password=socksPassword,
        )

    def parseStreamClient(self, *args, **kwargs):
        # for Twisted 14 and 15 (and more) the first argument is
        # 'reactor', for older Twisteds it's not
        return self._parseClient(*args, **kwargs)


def _maybe_unique_host(onion):
    """
    :param onion: IAuthenticatedOnionClients provider

    :returns: a .onion hostname if all clients have the same name or
        raises ValueError otherwise
    """
    hosts = [
        onion.get_client(nm).hostname
        for nm in onion.client_names()
    ]
    if not hosts:
        raise ValueError(
            "Can't access .onion_uri because there are no clients"
        )
    host = hosts[0]
    for h in hosts[1:]:
        if h != host:
            raise ValueError(
                "Cannot access .onion_uri for stealth-authenticated services "
                "because each client has a unique URI"
            )
    return host
