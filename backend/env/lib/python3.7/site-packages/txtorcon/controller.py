# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import os
import sys
import six
import shlex
import tempfile
import functools
from io import StringIO
from collections import Sequence
from os.path import dirname, exists

from twisted.python import log
from twisted.python.failure import Failure
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred, succeed, fail
from twisted.internet import protocol, error
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.endpoints import UNIXClientEndpoint
from twisted.internet.interfaces import IReactorTime, IReactorCore
from twisted.internet.interfaces import IStreamClientEndpoint

from zope.interface import implementer

from txtorcon.util import delete_file_or_tree, find_keywords
from txtorcon.util import find_tor_binary, available_tcp_port
from txtorcon.log import txtorlog
from txtorcon.torcontrolprotocol import TorProtocolFactory
from txtorcon.torstate import TorState
from txtorcon.torconfig import TorConfig
from txtorcon.endpoints import TorClientEndpoint, _create_socks_endpoint
from txtorcon.endpoints import TCPHiddenServiceEndpoint
from txtorcon.onion import EphemeralOnionService, FilesystemOnionService, _validate_ports
from txtorcon.util import _is_non_public_numeric_address

from . import socks
from .interface import ITor

try:
    from .controller_py3 import _AsyncOnionAuthContext
    HAVE_ASYNC = True
except Exception:
    HAVE_ASYNC = False

if sys.platform in ('linux', 'linux2', 'darwin'):
    import pwd


@inlineCallbacks
def launch(reactor,
           progress_updates=None,
           control_port=None,
           data_directory=None,
           socks_port=None,
           stdout=None,
           stderr=None,
           timeout=None,
           tor_binary=None,
           user=None,  # XXX like the config['User'] special-casing from before
           # 'users' probably never need these:
           connection_creator=None,
           kill_on_stderr=True,
           _tor_config=None,  # a TorConfig instance, mostly for tests
           ):
    """
    launches a new Tor process, and returns a Deferred that fires with
    a new :class:`txtorcon.Tor` instance. From this instance, you can
    create or get any "interesting" instances you need: the
    :class:`txtorcon.TorConfig` instance, create endpoints, create
    :class:`txtorcon.TorState` instance(s), etc.

    Note that there is NO way to pass in a config; we only expost a
    couple of basic Tor options. If you need anything beyond these,
    you can access the ``TorConfig`` instance (via ``.config``)
    and make any changes there, reflecting them in tor with
    ``.config.save()``.

    You can igore all the options and safe defaults will be
    provided. However, **it is recommended to pass data_directory**
    especially if you will be starting up Tor frequently, as it saves
    a bunch of time (and bandwidth for the directory
    authorities). "Safe defaults" means:

      - a tempdir for a ``DataDirectory`` is used (respecting ``TMP``)
        and is deleted when this tor is shut down (you therefore
        *probably* want to supply the ``data_directory=`` kwarg);
      - a random, currently-unused local TCP port is used as the
        ``SocksPort`` (specify ``socks_port=`` if you want your
        own). If you want no SOCKS listener at all, pass
        ``socks_port=0``
      - we set ``__OwningControllerProcess`` and call
        ``TAKEOWNERSHIP`` so that if our control connection goes away,
        tor shuts down (see `control-spec
        <https://gitweb.torproject.org/torspec.git/blob/HEAD:/control-spec.txt>`_
        3.23).
      - the launched Tor will use ``COOKIE`` authentication.

    :param reactor: a Twisted IReactorCore implementation (usually
        twisted.internet.reactor)

    :param progress_updates: a callback which gets progress updates; gets 3
         args: percent, tag, summary (FIXME make an interface for this).

    :param data_directory: set as the ``DataDirectory`` option to Tor,
        this is where tor keeps its state information (cached relays,
        etc); starting with an already-populated state directory is a lot
        faster. If ``None`` (the default), we create a tempdir for this
        **and delete it on exit**. It is recommended you pass something here.

    :param stdout: a file-like object to which we write anything that
        Tor prints on stdout (just needs to support write()).

    :param stderr: a file-like object to which we write anything that
        Tor prints on stderr (just needs .write()). Note that we kill
        Tor off by default if anything appears on stderr; pass
        "kill_on_stderr=False" if you don't want this behavior.

    :param tor_binary: path to the Tor binary to run. If None (the
        default), we try to find the tor binary.

    :param kill_on_stderr:
        When True (the default), if Tor prints anything on stderr we
        kill off the process, close the TorControlProtocol and raise
        an exception.

    :param connection_creator: is mostly available to ease testing, so
        you probably don't want to supply this. If supplied, it is a
        callable that should return a Deferred that delivers an
        :api:`twisted.internet.interfaces.IProtocol <IProtocol>` or
        ConnectError.
        See :api:`twisted.internet.interfaces.IStreamClientEndpoint`.connect
        Note that this parameter is ignored if config.ControlPort == 0

    :return: a Deferred which callbacks with :class:`txtorcon.Tor`
        instance, from which you can retrieve the TorControlProtocol
        instance via the ``.protocol`` property.

    HACKS:

     1. It's hard to know when Tor has both (completely!) written its
        authentication cookie file AND is listening on the control
        port. It seems that waiting for the first 'bootstrap' message on
        stdout is sufficient. Seems fragile...and doesn't work 100% of
        the time, so FIXME look at Tor source.



    XXX this "User" thing was, IIRC, a feature for root-using scripts
    (!!) that were going to launch tor, but where tor would drop to a
    different user. Do we still want to support this? Probably
    relevant to Docker (where everything is root! yay!)

    ``User``: if this exists, we attempt to set ownership of the tempdir
    to this user (but only if our effective UID is 0).
    """

    # We have a slight problem with the approach: we need to pass a
    # few minimum values to a torrc file so that Tor will start up
    # enough that we may connect to it. Ideally, we'd be able to
    # start a Tor up which doesn't really do anything except provide
    # "AUTHENTICATE" and "GETINFO config/names" so we can do our
    # config validation.

    if not IReactorCore.providedBy(reactor):
        raise ValueError(
            "'reactor' argument must provide IReactorCore"
            " (got '{}': {})".format(
                type(reactor).__class__.__name__,
                repr(reactor)
            )
        )

    if tor_binary is None:
        tor_binary = find_tor_binary()
    if tor_binary is None:
        # We fail right here instead of waiting for the reactor to start
        raise TorNotFound('Tor binary could not be found')

    # make sure we got things that have write() for stderr, stdout
    # kwargs (XXX is there a "better" way to check for file-like
    # object? do we use anything besides 'write()'?)
    for arg in [stderr, stdout]:
        if arg and not getattr(arg, "write", None):
            raise RuntimeError(
                'File-like object needed for stdout or stderr args.'
            )

    config = _tor_config or TorConfig()
    if data_directory is not None:
        user_set_data_directory = True
        config.DataDirectory = data_directory
        try:
            os.mkdir(data_directory, 0o0700)
        except OSError:
            pass
    else:
        user_set_data_directory = False
        data_directory = tempfile.mkdtemp(prefix='tortmp')
        config.DataDirectory = data_directory
        # note: we also set up the ProcessProtocol to delete this when
        # Tor exits, this is "just in case" fallback:
        reactor.addSystemEventTrigger(
            'before', 'shutdown',
            functools.partial(delete_file_or_tree, data_directory)
        )

    # things that used launch_tor() had to set ControlPort and/or
    # SocksPort on the config to pass them, so we honour that here.
    if control_port is None and _tor_config is not None:
        try:
            control_port = config.ControlPort
        except KeyError:
            control_port = None

    if socks_port is None and _tor_config is not None:
        try:
            socks_port = config.SocksPort
        except KeyError:
            socks_port = None

    if socks_port is None:
        socks_port = yield available_tcp_port(reactor)
    config.SOCKSPort = socks_port

    try:
        our_user = user or config.User
    except KeyError:
        pass
    else:
        # if we're root, make sure the directory is owned by the User
        # that Tor is configured to drop to
        if sys.platform in ('linux', 'linux2', 'darwin') and os.geteuid() == 0:
            os.chown(data_directory, pwd.getpwnam(our_user).pw_uid, -1)

    # user can pass in a control port, or we set one up here
    if control_port is None:
        # on posix-y systems, we can use a unix-socket
        if sys.platform in ('linux', 'linux2', 'darwin'):
            # note: tor will not accept a relative path for ControlPort
            control_port = 'unix:{}'.format(
                os.path.join(os.path.realpath(data_directory), 'control.socket')
            )
        else:
            control_port = yield available_tcp_port(reactor)
    else:
        if str(control_port).startswith('unix:'):
            control_path = control_port.lstrip('unix:')
            containing_dir = dirname(control_path)
            if not exists(containing_dir):
                raise ValueError(
                    "The directory containing '{}' must exist".format(
                        containing_dir
                    )
                )
            # Tor will be sad if the directory isn't 0700
            mode = (0o0777 & os.stat(containing_dir).st_mode)
            if mode & ~(0o0700):
                raise ValueError(
                    "The directory containing a unix control-socket ('{}') "
                    "must only be readable by the user".format(containing_dir)
                )
    config.ControlPort = control_port

    config.CookieAuthentication = 1
    config.__OwningControllerProcess = os.getpid()
    if connection_creator is None:
        if str(control_port).startswith('unix:'):
            connection_creator = functools.partial(
                UNIXClientEndpoint(reactor, control_port[5:]).connect,
                TorProtocolFactory()
            )
        else:
            connection_creator = functools.partial(
                TCP4ClientEndpoint(reactor, 'localhost', control_port).connect,
                TorProtocolFactory()
            )
    # not an "else" on purpose; if we passed in "control_port=0" *and*
    # a custom connection creator, we should still set this to None so
    # it's never called (since we can't connect with ControlPort=0)
    if control_port == 0:
        connection_creator = None

    # NOTE well, that if we don't pass "-f" then Tor will merrily load
    # its default torrc, and apply our options over top... :/ should
    # file a bug probably? --no-defaults or something maybe? (does
    # --defaults-torrc - or something work?)
    config_args = ['-f', '/dev/null/non-existant-on-purpose', '--ignore-missing-torrc']

    # ...now add all our config options on the command-line. This
    # avoids writing a temporary torrc.
    for (k, v) in config.config_args():
        config_args.append(k)
        config_args.append(v)

    process_protocol = TorProcessProtocol(
        connection_creator,
        progress_updates,
        config, reactor,
        timeout,
        kill_on_stderr,
        stdout,
        stderr,
    )
    if control_port == 0:
        connected_cb = succeed(None)
    else:
        connected_cb = process_protocol.when_connected()

    # we set both to_delete and the shutdown events because this
    # process might be shut down way before the reactor, but if the
    # reactor bombs out without the subprocess getting closed cleanly,
    # we'll want the system shutdown events triggered so the temporary
    # files get cleaned up either way

    # we don't want to delete the user's directories, just temporary
    # ones this method created.
    if not user_set_data_directory:
        process_protocol.to_delete = [data_directory]
        reactor.addSystemEventTrigger(
            'before', 'shutdown',
            functools.partial(delete_file_or_tree, data_directory)
        )

    log.msg('Spawning tor process with DataDirectory', data_directory)
    args = [tor_binary] + config_args
    transport = reactor.spawnProcess(
        process_protocol,
        tor_binary,
        args=args,
        env={'HOME': data_directory},
        path=data_directory if os.path.exists(data_directory) else None,  # XXX error if it doesn't exist?
    )
    transport.closeStdin()
    proto = yield connected_cb
    # note "proto" here is a TorProcessProtocol

    # we might need to attach this protocol to the TorConfig
    if config.protocol is None and proto is not None and proto.tor_protocol is not None:
        # proto is None in the ControlPort=0 case
        yield config.attach_protocol(proto.tor_protocol)
        # note that attach_protocol waits for the protocol to be
        # boostrapped if necessary

    returnValue(
        Tor(
            reactor,
            config.protocol,
            _tor_config=config,
            _process_proto=process_protocol,
        )
    )


@inlineCallbacks
def connect(reactor, control_endpoint=None, password_function=None):
    """
    Creates a :class:`txtorcon.Tor` instance by connecting to an
    already-running tor's control port. For example, a common default
    tor uses is UNIXClientEndpoint(reactor, '/var/run/tor/control') or
    TCP4ClientEndpoint(reactor, 'localhost', 9051)

    If only password authentication is available in the tor we connect
    to, the ``password_function`` is called (if supplied) to retrieve
    a valid password. This function can return a Deferred.

    For example::

        import txtorcon
        from twisted.internet.task import react
        from twisted.internet.defer import inlineCallbacks

        @inlineCallbacks
        def main(reactor):
            tor = yield txtorcon.connect(
                TCP4ClientEndpoint(reactor, "localhost", 9051)
            )
            state = yield tor.create_state()
            for circuit in state.circuits:
                print(circuit)

    :param control_endpoint: None, an IStreamClientEndpoint to connect
        to, or a Sequence of IStreamClientEndpoint instances to connect
        to. If None, a list of defaults are tried.

    :param password_function:
        See :class:`txtorcon.TorControlProtocol`

    :return:
        a Deferred that fires with a :class:`txtorcon.Tor` instance
    """

    @inlineCallbacks
    def try_endpoint(control_ep):
        assert IStreamClientEndpoint.providedBy(control_ep)
        proto = yield control_ep.connect(
            TorProtocolFactory(
                password_function=password_function
            )
        )
        config = yield TorConfig.from_protocol(proto)
        tor = Tor(reactor, proto, _tor_config=config)
        returnValue(tor)

    if control_endpoint is None:
        to_try = [
            UNIXClientEndpoint(reactor, '/var/run/tor/control'),
            TCP4ClientEndpoint(reactor, '127.0.0.1', 9051),
            TCP4ClientEndpoint(reactor, '127.0.0.1', 9151),
        ]
    elif IStreamClientEndpoint.providedBy(control_endpoint):
        to_try = [control_endpoint]
    elif isinstance(control_endpoint, Sequence):
        to_try = control_endpoint
        for ep in control_endpoint:
            if not IStreamClientEndpoint.providedBy(ep):
                raise ValueError(
                    "For control_endpoint=, '{}' must provide"
                    " IStreamClientEndpoint".format(ep)
                )
    else:
        raise ValueError(
            "For control_endpoint=, '{}' must provide"
            " IStreamClientEndpoint".format(control_endpoint)
        )

    errors = []
    for idx, ep in enumerate(to_try):
        try:
            tor = yield try_endpoint(ep)
            txtorlog.msg("Connected via '{}'".format(ep))
            returnValue(tor)
        except Exception as e:
            errors.append(e)
    if len(errors) == 1:
        raise errors[0]
    raise RuntimeError(
        'Failed to connect to: {}'.format(
            ', '.join(
                '{}: {}'.format(ep, err) for ep, err in zip(to_try, errors)
            )
        )
    )


@implementer(ITor)
class Tor(object):
    """
    I represent a single instance of Tor and act as a Builder/Factory
    for several useful objects you will probably want. There are two
    ways to create a Tor instance:

       - :func:`txtorcon.connect` to connect to a Tor that is already
         running (e.g. Tor Browser Bundle, a system Tor, ...).
       - :func:`txtorcon.launch` to launch a fresh Tor instance

    The stable API provided by this class is :class:`txtorcon.interface.ITor`

    If you desire more control, there are "lower level" APIs which are
    the very ones used by this class. However, this "highest level"
    API should cover many use-cases::

        import txtorcon

        @inlineCallbacks
        def main(reactor):
            # tor = yield txtorcon.connect(UNIXClientEndpoint(reactor, "/var/run/tor/control"))
            tor = yield txtorcon.launch(reactor)

            onion_ep = tor.create_onion_endpoint(port=80)
            port = yield onion_ep.listen(Site())
            print(port.getHost())
    """

    def __init__(self, reactor, control_protocol, _tor_config=None, _process_proto=None):
        """
        don't instantiate this class yourself -- instead use the factory
        methods :func:`txtorcon.launch` or :func:`txtorcon.connect`
        """
        self._protocol = control_protocol
        self._config = _tor_config
        self._reactor = reactor
        # this only passed/set when we launch()
        self._process_protocol = _process_proto
        # cache our preferred socks port (please use
        # self._default_socks_endpoint() to get one)
        self._socks_endpoint = None

    @inlineCallbacks
    def quit(self):
        """
        Closes the control connection, and if we launched this Tor
        instance we'll send it a TERM and wait until it exits.
        """
        if self._protocol is not None:
            yield self._protocol.quit()
        if self._process_protocol is not None:
            yield self._process_protocol.quit()
        if self._protocol is None and self._process_protocol is None:
            raise RuntimeError(
                "This Tor has no protocol instance; we can't quit"
            )
        if self._protocol is not None:
            yield self._protocol.on_disconnect

    @property
    def process(self):
        """
        An object implementing
        :api:`twisted.internet.interfaces.IProcessProtocol` if this
        Tor instance was launched, or None.
        """
        if self._process_protocol:
            return self._process_protocol
        return None

    @property
    def protocol(self):
        """
        The TorControlProtocol instance that is communicating with this
        Tor instance.
        """
        return self._protocol

    @property
    def version(self):
        return self._protocol.version

    @inlineCallbacks
    def get_config(self):
        """
        :return: a Deferred that fires with a TorConfig instance. This
            instance represents up-to-date configuration of the tor
            instance (even if another controller is connected). If you
            call this more than once you'll get the same TorConfig back.
        """
        if self._config is None:
            self._config = yield TorConfig.from_protocol(self._protocol)
        returnValue(self._config)

    def web_agent(self, pool=None, socks_endpoint=None):
        """
        :param socks_endpoint: If ``None`` (the default), a suitable
            SOCKS port is chosen from our config (or added). If supplied,
            should be a Deferred which fires an IStreamClientEndpoint
            (e.g. the return-value from
            :meth:`txtorcon.TorConfig.socks_endpoint`) or an immediate
            IStreamClientEndpoint You probably don't need to mess with
            this.

        :param pool: passed on to the Agent (as ``pool=``)
        """
        # local import since not all platforms have this
        from txtorcon import web

        if socks_endpoint is None:
            socks_endpoint = _create_socks_endpoint(self._reactor, self._protocol)
        if not isinstance(socks_endpoint, Deferred):
            if not IStreamClientEndpoint.providedBy(socks_endpoint):
                raise ValueError(
                    "'socks_endpoint' should be a Deferred or an IStreamClient"
                    "Endpoint (got '{}')".format(type(socks_endpoint))
                )
        return web.tor_agent(
            self._reactor,
            socks_endpoint,
            pool=pool,
        )

    @inlineCallbacks
    def dns_resolve(self, hostname):
        """
        :param hostname: a string

        :returns: a Deferred that calbacks with the hostname as looked-up
            via Tor (or errback).  This uses Tor's custom extension to the
            SOCKS5 protocol.
        """
        socks_ep = yield self._default_socks_endpoint()
        ans = yield socks.resolve(socks_ep, hostname)
        returnValue(ans)

    @inlineCallbacks
    def dns_resolve_ptr(self, ip):
        """
        :param ip: a string, like "127.0.0.1"

        :returns: a Deferred that calbacks with the IP address as
            looked-up via Tor (or errback).  This uses Tor's custom
            extension to the SOCKS5 protocol.
        """
        socks_ep = yield self._default_socks_endpoint()
        ans = yield socks.resolve_ptr(socks_ep, ip)
        returnValue(ans)

    @inlineCallbacks
    def add_onion_authentication(self, onion_host, token):
        """
        Add a client-side authentication token for a particular Onion
        service.
        """
        # if we add the same onion twice, Tor rejects us. We throw an
        # error if we already have that .onion but the incoming token
        # doesn't match
        if isinstance(onion_host, bytes):
            onion_host = onion_host.decode('ascii')

        config = yield self.get_config()
        tokens = {
            servauth.split()[0]: servauth.split()[1]
            for servauth in config.HidServAuth
        }
        try:
            maybe_token = tokens[onion_host]
            if maybe_token != token:
                raise ValueError(
                    "Token conflict for host '{}'".format(onion_host)
                )
            return
        except KeyError:
            pass

        # add our onion + token combo
        config.HidServAuth.append(
            u"{} {}".format(onion_host, token)
        )
        yield config.save()

    @inlineCallbacks
    def remove_onion_authentication(self, onion_host):
        """
        Remove a token for an onion host

        :returns: True if successful, False if there wasn't a token
            for that host.
        """
        if isinstance(onion_host, bytes):
            onion_host = onion_host.decode('ascii')

        config = yield self.get_config()
        to_remove = None
        for auth in config.HidServAuth:
            host, token = auth.split()
            if host == onion_host:
                to_remove = auth

        if to_remove is not None:
            config.HidServAuth.remove(to_remove)
            yield config.save()
            returnValue(True)
        returnValue(False)

    def onion_authentication(self, onion_host, token):
        """
        (Python3 only!) This returns an async context-manager that will
        add and remove onion authentication. For example, inside an
        `async def` method that's had `ensureDeferred` called on it::

            async with tor.onion_authentication("timaq4ygg2iegci7.onion", "seekrit token"):
                agent = tor.web_agent()
                resp = await agent.request(b'GET', "http://timaq4ygg2iegci7.onion/")
                body = await readBody(resp)
            # after the "async with" the token will be removed from Tor's configuration

        Under the hood, this just uses the add_onion_authentication
        and remove_onion_authentication methods so on Python2 you can
        use those together with try/finally to get the same effect.
        """
        if not HAVE_ASYNC:
            raise RuntimeError(
                "async context-managers not supported in Python3.4 or lower"
            )
        return _AsyncOnionAuthContext(
            self, onion_host, token
        )

    def stream_via(self, host, port, tls=False, socks_endpoint=None):
        """
        This returns an IStreamClientEndpoint_ instance that will use this
        Tor (via SOCKS) to visit the ``(host, port)`` indicated.

        :param host: The host to connect to. You MUST pass host-names
            to this. If you absolutely know that you've not leaked DNS
            (e.g. you save IPs in your app's configuration or similar)
            then you can pass an IP.

        :param port: Port to connect to.

        :param tls: If True, it will wrap the return endpoint in one
            that does TLS (default: False).

        :param socks_endpoint: Normally not needed (default: None)
            but you can pass an IStreamClientEndpoint_ directed at one
            of the local Tor's SOCKS5 ports (e.g. created with
            :meth:`txtorcon.TorConfig.create_socks_endpoint`). Can be
            a Deferred.

        .. _IStreamClientEndpoint: https://twistedmatrix.com/documents/current/api/twisted.internet.interfaces.IStreamClientEndpoint.html
        """
        if _is_non_public_numeric_address(host):
            raise ValueError("'{}' isn't going to work over Tor".format(host))

        if socks_endpoint is None:
            socks_endpoint = self._default_socks_endpoint()
        # socks_endpoint may be a a Deferred, but TorClientEndpoint handles it
        return TorClientEndpoint(
            host, port,
            socks_endpoint=socks_endpoint,
            tls=tls,
            reactor=self._reactor,
        )

    def create_authenticated_onion_endpoint(self, port, auth, private_key=None, version=None):
        """
        WARNING: API subject to change

        When creating an authenticated Onion service a token is
        created for each user. For 'stealth' authentication, the
        hostname is also different for each user. The difference between
        this method and :meth:`txtorcon.Tor.create_onion_endpoint` is
        in this case the "onion_service" instance implements
        :class:`txtorcon.IAuthenticatedOnionClients`.

        :returns: an object that implements IStreamServerEndpoint,
            which will create an "ephemeral" Onion service when
            ``.listen()`` is called. This uses the ``ADD_ONION`` Tor
            control-protocol command. The object returned from
            ``.listen()`` will be a :class:TorOnionListeningPort``;
            its ``.onion_service`` attribute will be a
            :class:`txtorcon.IAuthenticatedOnionClients` instance.

        :param port: the port to listen publically on the Tor network
           on (e.g. 80 for a Web server)

        :param private_key: if not None (the default), this should be
            the same blob of key material that you received from the
            :class:`txtorcon.IOnionService` object during a previous
            run (i.e. from the ``.provate_key`` attribute).

        :param version: if not None, a specific version of service to
            use; version=3 is Proposition 224 and version=2 is the
            older 1024-bit key based implementation.

        :param auth: a AuthBasic or AuthStealth instance
        """
        return TCPHiddenServiceEndpoint(
            self._reactor, self.get_config(), port,
            hidden_service_dir=None,
            local_port=None,
            ephemeral=True,
            private_key=private_key,
            version=version,
            auth=auth,
        )

    def create_onion_endpoint(self, port, private_key=None, version=None, single_hop=None):
        """
        WARNING: API subject to change

        :returns: an object that implements IStreamServerEndpoint,
            which will create an "ephemeral" Onion service when
            ``.listen()`` is called. This uses the ``ADD_ONION`` tor
            control-protocol command. The object returned from
            ``.listen()`` will be a :class:TorOnionListeningPort``;
            its ``.onion_service`` attribute will be a
            :class:`txtorcon.IOnionService` instance.

        :param port: the port to listen publically on the Tor network
           on (e.g. 80 for a Web server)

        :param private_key: if not None (the default), this should be
            the same blob of key material that you received from the
            :class:`txtorcon.IOnionService` object during a previous
            run (i.e. from the ``.private_key`` attribute).

        :param version: if not None, a specific version of service to
            use; version=3 is Proposition 224 and version=2 is the
            older 1024-bit key based implementation.

        :param single_hop: if True, pass the `NonAnonymous` flag. Note
            that Tor options `HiddenServiceSingleHopMode`,
            `HiddenServiceNonAnonymousMode` must be set to `1` and there
            must be no `SOCKSPort` configured for this to actually work.
        """
        # note, we're just depending on this being The Ultimate
        # Everything endpoint. Which seems fine, because "normal"
        # users should use this or another factory-method to
        # instantiate them...
        return TCPHiddenServiceEndpoint(
            self._reactor, self.get_config(), port,
            hidden_service_dir=None,
            local_port=None,
            ephemeral=True,
            private_key=private_key,
            version=version,
            auth=None,
            single_hop=single_hop,
        )

    def create_filesystem_onion_endpoint(self, port, hs_dir, group_readable=False, version=None):
        """
        WARNING: API subject to change

        :returns: an object that implements IStreamServerEndpoint. When
            the ``.listen()`` method is called, the endpoint will create
            an Onion service whose keys are on disk when ``.listen()`` is
            called. The object returned from ``.listen()`` will be a
            :class:TorOnionListeningPort``; its ``.onion_service``
            attribute will be a :class:`txtorcon.IOnionService` instance.

        :param port: the port to listen publically on the Tor network
           on (e.g. 80 for a Web server)

        :param hs_dir: the directory in which keys are stored for this
            service.

        :param group_readable: controls the Tor
            `HiddenServiceDirGroupReadable` which will either set (or not)
            group read-permissions on the hs_dir.

        :param version: if not None, a specific version of service to
            use; version=3 is Proposition 224 and version=2 is the
            older 1024-bit key based implementation. The default is version 3.
        """
        return TCPHiddenServiceEndpoint(
            self._reactor, self.get_config(), port,
            hidden_service_dir=hs_dir,
            local_port=None,
            ephemeral=False,
            private_key=None,
            group_readable=int(group_readable),
            version=version,
            auth=None,
        )

    def create_filesystem_authenticated_onion_endpoint(self, port, hs_dir, auth, group_readable=False, version=None):
        """
        WARNING: API subject to change

        :returns: an object that implements IStreamServerEndpoint. When
            the ``.listen()`` method is called, the endpoint will create
            an Onion service whose keys are on disk when ``.listen()`` is
            called. The object returned from ``.listen()`` will be a
            :class:TorOnionListeningPort``; its ``.onion_service``
            attribute will be a :class:`txtorcon.IOnionService` instance.

        :param port: the port to listen publically on the Tor network
           on (e.g. 80 for a Web server)

        :param hs_dir: the directory in which keys are stored for this
            service.

        :param auth: instance of :class:`txtorcon.AuthBasic` or
            :class:`txtorcon.AuthStealth` controlling the type of
            authentication to use.

        :param group_readable: controls the Tor
            `HiddenServiceDirGroupReadable` which will either set (or not)
            group read-permissions on the hs_dir.

        :param version: if not None, a specific version of service to
            use; version=3 is Proposition 224 and version=2 is the
            older 1024-bit key based implementation. The default is version 3.
        """
        return TCPHiddenServiceEndpoint(
            self._reactor, self.get_config(), port,
            hidden_service_dir=hs_dir,
            local_port=None,
            ephemeral=False,
            private_key=None,
            group_readable=int(group_readable),
            version=version,
            auth=auth,
        )

    # XXX or get_state()? and make there be always 0 or 1 states; cf. convo w/ Warner
    @inlineCallbacks
    def create_state(self):
        """
        returns a Deferred that fires with a ready-to-go
        :class:`txtorcon.TorState` instance.
        """
        state = TorState(self.protocol)
        yield state.post_bootstrap
        returnValue(state)

    def __str__(self):
        return "<Tor version='{tor_version}'>".format(
            tor_version=self._protocol.version,
        )

    @inlineCallbacks
    def is_ready(self):
        """
        :return: a Deferred that fires with True if this Tor is
            non-dormant and ready to go. This will return True if `GETINFO
            dormant` is false or if `GETINFO status/enough-dir-info` is
            true or if `GETINFO status/circuit-established` true.
        """
        info = yield self.protocol.get_info(
            "dormant",
            "status/enough-dir-info",
            "status/circuit-established",
        )
        returnValue(
            not(
                int(info["dormant"]) or
                not int(info["status/enough-dir-info"]) or
                not int(info["status/circuit-established"])
            )
        )

    @inlineCallbacks
    def become_ready(self):
        """
        Make sure Tor is no longer dormant.

        If Tor is currently dormant, it is woken up by doing a DNS
        request for torproject.org
        """
        ready = yield self.is_ready()
        if not ready:
            yield self.dns_resolve(u'torproject.org')
        return

    @inlineCallbacks
    def _default_socks_endpoint(self):
        """
        Returns a Deferred that fires with our default SOCKS endpoint
        (which might mean setting one up in our attacked Tor if it
        doesn't have one)
        """
        if self._socks_endpoint is None:
            self._socks_endpoint = yield _create_socks_endpoint(self._reactor, self._protocol)
        returnValue(self._socks_endpoint)

    # For all these create_*() methods, instead of magically computing
    # the class-name from arguments (e.g. we could decide "it's a
    # Filesystem thing" if "hidden_service_dir=" is passed) we have an
    # explicit method for each type of service. This means each method
    # always returns the same type of object (good!) and user-code is
    # more explicit about what they want (also good!) .. but the
    # method names are kind of long (not-ideal)

    @inlineCallbacks
    def create_onion_service(self, ports, private_key=None, version=3, progress=None, await_all_uploads=False, single_hop=None):
        """
        Create a new Onion service

        This method will create a new Onion service, returning (via
        Deferred) an instance that implements IOnionService. (To
        create authenticated onion services, see XXX). This method
        awaits at least one upload of the Onion service's 'descriptor'
        to the Tor network -- this can take from 30s to a couple
        minutes.

        :param private_key: None, ``txtorcon.DISCARD`` or a key-blob
            retained from a prior run

            Passing ``None`` means a new one will be created. It can be
            retrieved from the ``.private_key`` property of the returned
            object. You **must** retain this key yourself (and pass it in
            to this method in the future) if you wish to keep the same
            ``.onion`` domain when re-starting your program.

            Passing ``txtorcon.DISCARD`` means txtorcon will never learn the
            private key from Tor and so there will be no way to re-create
            an Onion Service on the same address after Tor exits.

        :param version: The latest Tor releases support 'Proposition
            224' (version 3) services. These are the default.

        :param progress: if provided, a function that takes 3
            arguments: ``(percent_done, tag, description)`` which may
            be called any number of times to indicate some progress has
            been made.

        :param await_all_uploads: if False (the default) then we wait
            until at least one upload of our Descriptor to a Directory
            Authority has completed; if True we wait until all have
            completed.

        :param single_hop: if True, pass the `NonAnonymous` flag. Note
            that Tor options `HiddenServiceSingleHopMode`,
            `HiddenServiceNonAnonymousMode` must be set to `1` and there
            must be no `SOCKSPort` configured for this to actually work.
        """
        if version not in (2, 3):
            raise ValueError(
                "The only valid Onion service versions are 2 or 3"
            )
        if not isinstance(ports, Sequence) or isinstance(ports, six.string_types):
            raise ValueError("'ports' must be a sequence (list, tuple, ..)")

        processed_ports = yield _validate_ports(self._reactor, ports)
        config = yield self.get_config()
        service = yield EphemeralOnionService.create(
            reactor=self._reactor,
            config=config,
            ports=processed_ports,
            private_key=private_key,
            version=version,
            progress=progress,
            await_all_uploads=await_all_uploads,
            single_hop=single_hop,
        )
        returnValue(service)

    @inlineCallbacks
    def create_filesystem_onion_service(self, ports, onion_service_dir,
                                        version=3,
                                        group_readable=False,
                                        progress=None,
                                        await_all_uploads=False):
        """Create a new Onion service stored on disk

        This method will create a new Onion service, returning (via
        Deferred) an instance that implements IOnionService. (To
        create authenticated onion services, see XXX). This method
        awaits at least one upload of the Onion service's 'descriptor'
        to the Tor network -- this can take from 30s to a couple
        minutes.

        :param ports: a collection of ports to advertise; these are
            forwarded locally on a random port. Each entry may instead be
            a 2-tuple, which chooses an explicit local port.

        :param onion_service_dir: a path to an Onion Service
            directory.

            Tor will write a ``hostname`` file in this directory along
            with the private keys for the service (if they do not already
            exist). You do not need to retain the private key yourself.

        :param version: which kind of Onion Service to create. The
            default is ``3`` which are the Proposition 224
            services. Version ``2`` are the previous services. There are
            no other valid versions currently.

        :param group_readable: if True, Tor creates the directory with
           group read permissions. The default is False.

        :param progress: if provided, a function that takes 3
            arguments: ``(percent_done, tag, description)`` which may
            be called any number of times to indicate some progress has
            been made.

        """
        if not isinstance(ports, Sequence) or isinstance(ports, six.string_types):
            raise ValueError("'ports' must be a sequence (list, tuple, ..)")
        processed_ports = yield _validate_ports(self._reactor, ports)

        if version not in (2, 3):
            raise ValueError(
                "The only valid Onion service versions are 2 or 3"
            )
        config = yield self.get_config()
        service = yield FilesystemOnionService.create(
            reactor=self._reactor,
            config=config,
            hsdir=onion_service_dir,
            ports=processed_ports,
            version=version,
            group_readable=group_readable,
            progress=progress,
            await_all_uploads=await_all_uploads,
        )
        returnValue(service)


class TorNotFound(RuntimeError):
    """
    Raised by launch_tor() in case the tor binary was unspecified and could
    not be found by consulting the shell.
    """


class TorProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, connection_creator, progress_updates=None, config=None,
                 ireactortime=None, timeout=None, kill_on_stderr=True,
                 stdout=None, stderr=None):
        """
        This will read the output from a Tor process and attempt a
        connection to its control port when it sees any 'Bootstrapped'
        message on stdout. You probably don't need to use this
        directly except as the return value from the
        :func:`txtorcon.launch_tor` method. tor_protocol contains a
        valid :class:`txtorcon.TorControlProtocol` instance by that
        point.

        connection_creator is a callable that should return a Deferred
        that callbacks with a :class:`txtorcon.TorControlProtocol`;
        see :func:`txtorcon.launch_tor` for the default one which is a
        functools.partial that will call
        ``connect(TorProtocolFactory())`` on an appropriate
        :api:`twisted.internet.endpoints.TCP4ClientEndpoint`

        :param connection_creator: A no-parameter callable which
            returns a Deferred which promises a
            :api:`twisted.internet.interfaces.IStreamClientEndpoint
            <IStreamClientEndpoint>`. If this is None, we do NOT
            attempt to connect to the underlying Tor process.

        :param progress_updates: A callback which received progress
            updates with three args: percent, tag, summary

        :param config: a TorConfig object to connect to the
            TorControlProtocl from the launched tor (should it succeed)

        :param ireactortime:
            An object implementing IReactorTime (i.e. a reactor) which
            needs to be supplied if you pass a timeout.

        :param timeout:
            An int representing the timeout in seconds. If we are
            unable to reach 100% by this time we will consider the
            setting up of Tor to have failed. Must supply ireactortime
            if you supply this.

        :param kill_on_stderr:
            When True, kill subprocess if we receive anything on stderr

        :param stdout:
            Anything subprocess writes to stdout is sent to .write() on this

        :param stderr:
            Anything subprocess writes to stderr is sent to .write() on this

        :ivar tor_protocol: The TorControlProtocol instance connected
            to the Tor this
            :api:`twisted.internet.protocol.ProcessProtocol
            <ProcessProtocol>`` is speaking to. Will be valid after
            the Deferred returned from
            :meth:`TorProcessProtocol.when_connected` is triggered.
        """

        self.config = config
        self.tor_protocol = None
        self.progress_updates = progress_updates

        # XXX if connection_creator is not None .. is connected_cb
        # tied to connection_creator...?
        if connection_creator:
            self.connection_creator = connection_creator
        else:
            self.connection_creator = None
        # use SingleObserver
        self._connected_listeners = []  # list of Deferred (None when we're connected)

        self.attempted_connect = False
        self.to_delete = []
        self.kill_on_stderr = kill_on_stderr
        self.stderr = stderr
        self.stdout = stdout
        self.collected_stdout = StringIO()

        self._setup_complete = False
        self._did_timeout = False
        self._timeout_delayed_call = None
        self._on_exit = []  # Deferred's we owe a call/errback to when we exit
        if timeout:
            if not ireactortime:
                raise RuntimeError(
                    'Must supply an IReactorTime object when supplying a '
                    'timeout')
            ireactortime = IReactorTime(ireactortime)
            self._timeout_delayed_call = ireactortime.callLater(
                timeout, self._timeout_expired)

    def when_connected(self):
        if self._connected_listeners is None:
            return succeed(self)
        d = Deferred()
        self._connected_listeners.append(d)
        return d

    def _maybe_notify_connected(self, arg):
        """
        Internal helper.

        .callback or .errback on all Deferreds we've returned from
        `when_connected`
        """
        if self._connected_listeners is None:
            return
        for d in self._connected_listeners:
            # Twisted will turn this into an errback if "arg" is a
            # Failure
            d.callback(arg)
        self._connected_listeners = None

    def quit(self):
        """
        This will terminate (with SIGTERM) the underlying Tor process.

        :returns: a Deferred that callback()'s (with None) when the
            process has actually exited.
        """

        try:
            self.transport.signalProcess('TERM')
            d = Deferred()
            self._on_exit.append(d)

        except error.ProcessExitedAlready:
            self.transport.loseConnection()
            d = succeed(None)
        except Exception:
            d = fail()
        return d

    def _signal_on_exit(self, reason):
        to_notify = self._on_exit
        self._on_exit = []
        for d in to_notify:
            d.callback(None)

    def outReceived(self, data):
        """
        :api:`twisted.internet.protocol.ProcessProtocol <ProcessProtocol>` API
        """

        if self.stdout:
            self.stdout.write(data.decode('ascii'))

        # minor hack: we can't try this in connectionMade because
        # that's when the process first starts up so Tor hasn't
        # opened any ports properly yet. So, we presume that after
        # its first output we're good-to-go. If this fails, we'll
        # reset and try again at the next output (see this class'
        # tor_connection_failed)
        txtorlog.msg(data)
        if not self.attempted_connect and self.connection_creator \
                and b'Bootstrap' in data:
            self.attempted_connect = True
            # hmmm, we don't "do" anything with this Deferred?
            # (should it be connected to the when_connected
            # Deferreds?)
            d = self.connection_creator()
            d.addCallback(self._tor_connected)
            d.addErrback(self._tor_connection_failed)
# XXX 'should' be able to improve the error-handling by directly tying
# this Deferred into the notifications -- BUT we might try again, so
# we need to know "have we given up -- had an error" and only in that
# case send to the connected things. I think?
#            d.addCallback(self._maybe_notify_connected)

    def _timeout_expired(self):
        """
        A timeout was supplied during setup, and the time has run out.
        """
        self._did_timeout = True
        try:
            self.transport.signalProcess('TERM')
        except error.ProcessExitedAlready:
            # XXX why don't we just always do this?
            self.transport.loseConnection()

        fail = Failure(RuntimeError("timeout while launching Tor"))
        self._maybe_notify_connected(fail)

    def errReceived(self, data):
        """
        :api:`twisted.internet.protocol.ProcessProtocol <ProcessProtocol>` API
        """

        if self.stderr:
            self.stderr.write(data)

        if self.kill_on_stderr:
            self.transport.loseConnection()
            raise RuntimeError(
                "Received stderr output from slave Tor process: " + data)

    def cleanup(self):
        """
        Clean up my temporary files.
        """

        all([delete_file_or_tree(f) for f in self.to_delete])
        self.to_delete = []

    def processExited(self, reason):
        self._signal_on_exit(reason)

    def processEnded(self, status):
        """
        :api:`twisted.internet.protocol.ProcessProtocol <ProcessProtocol>` API
        """
        self.cleanup()

        if status.value.exitCode is None:
            if self._did_timeout:
                err = RuntimeError("Timeout waiting for Tor launch.")
            else:
                err = RuntimeError(
                    "Tor was killed (%s)." % status.value.signal)
        else:
            err = RuntimeError(
                "Tor exited with error-code %d" % status.value.exitCode)

        # hmmm, this log() should probably go away...not always an
        # error (e.g. .quit()
        log.err(err)
        self._maybe_notify_connected(Failure(err))

    def progress(self, percent, tag, summary):
        """
        Can be overridden or monkey-patched if you want to get
        progress updates yourself.
        """

        if self.progress_updates:
            self.progress_updates(percent, tag, summary)

    # the below are all callbacks

    def _tor_connection_failed(self, failure):
        # FIXME more robust error-handling please, like a timeout so
        # we don't just wait forever after 100% bootstrapped (that
        # is, we're ignoring these errors, but shouldn't do so after
        # we'll stop trying)
        # XXX also, should check if the failure is e.g. a syntax error
        # or an actually connection failure

        # okay, so this is a little trickier than I thought at first:
        # we *can* just relay this back to the
        # connection_creator()-returned Deferred, *but* we don't know
        # if this is "the last" error and we're going to try again
        # (and thus e.g. should fail all the when_connected()
        # Deferreds) or not.
        log.err(failure)
        self.attempted_connect = False
        return None

    def _status_client(self, arg):
        args = shlex.split(arg)
        if args[1] != 'BOOTSTRAP':
            return

        kw = find_keywords(args)
        prog = int(kw['PROGRESS'])
        tag = kw['TAG']
        summary = kw['SUMMARY']
        self.progress(prog, tag, summary)

        if prog == 100:
            if self._timeout_delayed_call:
                self._timeout_delayed_call.cancel()
                self._timeout_delayed_call = None
            self._maybe_notify_connected(self)

    @inlineCallbacks
    def _tor_connected(self, proto):
        txtorlog.msg("tor_connected %s" % proto)

        self.tor_protocol = proto
        self.tor_protocol.is_owned = self.transport.pid

        yield self.tor_protocol.post_bootstrap
        txtorlog.msg("Protocol is bootstrapped")
        yield self.tor_protocol.add_event_listener('STATUS_CLIENT', self._status_client)
        yield self.tor_protocol.queue_command('TAKEOWNERSHIP')
        yield self.tor_protocol.queue_command('RESETCONF __OwningControllerProcess')
        if self.config is not None and self.config.protocol is None:
            yield self.config.attach_protocol(proto)
        returnValue(self)  # XXX or "proto"?
