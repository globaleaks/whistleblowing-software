# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

import six
import time
from datetime import datetime

from twisted.python.failure import Failure
from twisted.python import log
from twisted.internet import defer
from twisted.internet.interfaces import IStreamClientEndpoint
from zope.interface import implementer

from .interface import IRouterContainer, IStreamAttacher
from txtorcon.util import find_keywords, maybe_ip_addr, SingleObserver


# look like "2014-01-25T02:12:14.593772"
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


def _extract_reason(kw):
    """
    Internal helper. Extracts a reason (possibly both reasons!) from
    the kwargs for a circuit failed or closed event.
    """
    try:
        # we "often" have a REASON
        reason = kw['REASON']
        try:
            # ...and sometimes even have a REMOTE_REASON
            reason = '{}, {}'.format(reason, kw['REMOTE_REASON'])
        except KeyError:
            pass  # should still be the 'REASON' error if we had it
    except KeyError:
        reason = "unknown"
    return reason


@implementer(IStreamAttacher)
class _CircuitAttacher(object):
    """
    Internal helper.

    If we've ever called .stream_via or .web_agent, then one of these
    is added as "the" stream-attacher.
    """
    def __init__(self):
        # map real_host (IPAddress) -> circuit
        self._circuit_targets = dict()

    def add_endpoint(self, target_ep, circuit):
        """
        Returns a Deferred that fires when we've attached this endpoint to
        the provided circuit.
        """
        # This can seem a little .. convulted. What's going on is
        # we're asking the TorCircuitEndpoint to tell us when it gets
        # the local address (i.e. when "whomever created the endpoit"
        # actually connects locally). We need this address to
        # successfully map incoming streams.
        d = defer.Deferred()
        target_ep._get_address().addCallback(self._add_real_target, circuit, d)
        return d

    def _add_real_target(self, real_addr, circuit, d):
        # joy oh joy, ipaddress wants unicode, Twisted gives us bytes...
        real_host = maybe_ip_addr(six.text_type(real_addr.host))
        real_port = real_addr.port
        self._circuit_targets[(real_host, real_port)] = (circuit, d)

    def attach_stream_failure(self, stream, fail):
        """
        IStreamAttacher API
        """
        k = (stream.source_addr, stream.source_port)
        try:
            (circ, d) = self._circuit_targets.pop(k)
            d.errback(fail)
        except KeyError:
            pass
        # so this means ... we got an error, but on a stream we either
        # don't care about or already .callback()'d so should we log
        # it? or ignore?
        return None

    @defer.inlineCallbacks
    def attach_stream(self, stream, circuits):
        """
        IStreamAttacher API
        """

        k = (stream.source_addr, stream.source_port)
        try:
            circuit, d = self._circuit_targets.pop(k)
        except KeyError:
            return

        try:
            yield circuit.when_built()
            if circuit.state in ['FAILED', 'CLOSED', 'DETACHED']:
                d.errback(Failure(RuntimeError(
                    "Circuit {circuit.id} in state {circuit.state} so unusable".format(
                        circuit=circuit,
                    )
                )))
                return
            d.callback(None)
            defer.returnValue(circuit)
        except Exception:
            d.errback(Failure())


@defer.inlineCallbacks
def _get_circuit_attacher(reactor, state):
    if _get_circuit_attacher.attacher is None:
        _get_circuit_attacher.attacher = _CircuitAttacher()
        yield state.set_attacher(_get_circuit_attacher.attacher, reactor)
    defer.returnValue(_get_circuit_attacher.attacher)


_get_circuit_attacher.attacher = None


@implementer(IStreamClientEndpoint)
class TorCircuitEndpoint(object):
    def __init__(self, reactor, torstate, circuit, target_endpoint):
        self._reactor = reactor
        self._state = torstate
        self._target_endpoint = target_endpoint  # a TorClientEndpoint
        self._circuit = circuit

    @defer.inlineCallbacks
    def connect(self, protocol_factory):
        """IStreamClientEndpoint API"""
        # need to:
        # 1. add 'our' attacher to state
        # 2. do the "underlying" connect
        # 3. recognize our stream
        # 4. attach it to our circuit

        attacher = yield _get_circuit_attacher(self._reactor, self._state)
        # note that we'll only ever add an attacher once, and then it
        # stays there "forever". so if you never call the .stream_via
        # or .web_agent APIs, set_attacher won't get called .. but if
        # you *do*, then you can't call set_attacher yourself (because
        # that's an error). See discussion in set_attacher on
        # TorState or issue #169

        yield self._circuit.when_built()
        connect_d = self._target_endpoint.connect(protocol_factory)
        attached_d = attacher.add_endpoint(self._target_endpoint, self._circuit)
        proto = yield connect_d
        yield attached_d
        defer.returnValue(proto)


class Circuit(object):
    """
    Used by :class:`txtorcon.TorState` to represent one of Tor's circuits.

    This is kept up-to-date by the :class`txtorcon.TorState` that owns it, and
    individual circuits can be listened to for updates (or listen to
    every one using :meth:`txtorcon.TorState.add_circuit_listener`)

    :ivar path:
        contains a list of :class:`txtorcon.Router` objects
        representing the path this Circuit takes. Mostly this will be
        3 or 4 routers long. Note that internally Tor uses single-hop
        paths for some things. See also the *purpose*
        instance-variable.

    :ivar streams:
        contains a list of Stream objects representing all streams
        currently attached to this circuit.

    :ivar state:
        contains a string from Tor describing the current state of the
        stream. From control-spec.txt section 4.1.1, these are:

            - LAUNCHED: circuit ID assigned to new circuit
            - BUILT: all hops finished, can now accept streams
            - EXTENDED: one more hop has been completed
            - FAILED: circuit closed (was not built)
            - CLOSED: circuit closed (was built)

    :ivar purpose:
        The reason this circuit was built. For most purposes, you'll
        want to look at `GENERAL` circuits only. Values can currently
        be one of (but see control-spec.txt 4.1.1):

            - GENERAL
            - HS_CLIENT_INTRO
            - HS_CLIENT_REND
            - HS_SERVICE_INTRO
            - HS_SERVICE_REND
            - TESTING
            - CONTROLLER

    :ivar id: The ID of this circuit, a number (or None if unset).

    """

    def __init__(self, routercontainer):
        """
        :param routercontainer:
            should implement :class:`txtorcon.interface.IRouterContainer`.
        """
        self.listeners = []
        self.router_container = IRouterContainer(routercontainer)
        self._torstate = routercontainer  # XXX FIXME
        self.path = []
        self.streams = []
        self.purpose = None
        self.id = None
        self.state = 'UNKNOWN'
        self.build_flags = []
        self.flags = {}

        # this is used to hold a Deferred that will callback() when
        # this circuit is being CLOSED or FAILED.
        self._closing_deferred = None
        # XXX ^ should probably be when_closed() etc etc...

        # caches parsed value for time_created()
        self._time_created = None

        # all notifications for when_built, when_closed
        self._when_built = SingleObserver()
        self._when_closed = SingleObserver()

    # XXX backwards-compat for old .is_built for now
    @property
    def is_built(self):
        return self.when_built()

    def when_built(self):
        """
        Returns a Deferred that is callback()'d (with this Circuit
        instance) when this circuit hits BUILT.

        If it's already BUILT when this is called, you get an
        already-successful Deferred; otherwise, the state must change
        to BUILT.

        If the circuit will never hit BUILT (e.g. it is abandoned by
        Tor before it gets to BUILT) you will receive an errback
        """
        # XXX note to self: we never do an errback; fix this behavior
        if self.state == 'BUILT':
            return defer.succeed(self)
        return self._when_built.when_fired()

    def when_closed(self):
        """
        Returns a Deferred that callback()'s (with this Circuit instance)
        when this circuit hits CLOSED or FAILED.
        """
        if self.state in ['CLOSED', 'FAILED']:
            return defer.succeed(self)
        return self._when_closed.when_fired()

    def web_agent(self, reactor, socks_endpoint, pool=None):
        """
        :param socks_endpoint: create one with
            :meth:`txtorcon.TorConfig.create_socks_endpoint`. Can be a
            Deferred.

        :param pool: passed on to the Agent (as ``pool=``)
        """
        # local import because there isn't Agent stuff on some
        # platforms we support, so this will only error if you try
        # this on the wrong platform (pypy [??] and old-twisted)
        from txtorcon import web
        return web.tor_agent(
            reactor,
            socks_endpoint,
            circuit=self,
            pool=pool,
        )

    # XXX should make this API match above web_agent (i.e. pass a
    # socks_endpoint) or change the above...
    def stream_via(self, reactor, host, port,
                   socks_endpoint,
                   use_tls=False):
        """
        This returns an `IStreamClientEndpoint`_ that will connect to
        the given ``host``, ``port`` via Tor -- and via this
        parciular circuit.

        We match the streams up using their source-ports, so even if
        there are many streams in-flight to the same destination they
        will align correctly. For example, to cause a stream to go to
        ``torproject.org:443`` via a particular circuit::

            @inlineCallbacks
            def main(reactor):
                circ = yield torstate.build_circuit()  # lets Tor decide the path
                yield circ.when_built()
                tor_ep = circ.stream_via(reactor, 'torproject.org', 443)
                # 'factory' is for your protocol
                proto = yield tor_ep.connect(factory)

        Note that if you're doing client-side Web requests, you
        probably want to use `treq
        <http://treq.readthedocs.org/en/latest/>`_ or ``Agent``
        directly so call :meth:`txtorcon.Circuit.web_agent` instead.

        :param socks_endpoint: should be a Deferred firing a valid
            IStreamClientEndpoint pointing at a Tor SOCKS port (or an
            IStreamClientEndpoint already).

        .. _istreamclientendpoint: https://twistedmatrix.com/documents/current/api/twisted.internet.interfaces.IStreamClientEndpoint.html
        """
        from .endpoints import TorClientEndpoint
        ep = TorClientEndpoint(
            host, port, socks_endpoint,
            tls=use_tls,
            reactor=reactor,
        )
        return TorCircuitEndpoint(reactor, self._torstate, self, ep)

    @property
    def time_created(self):
        if self._time_created is not None:
            return self._time_created
        if 'TIME_CREATED' in self.flags:
            # strip off milliseconds
            t = self.flags['TIME_CREATED'].split('.')[0]
            tstruct = time.strptime(t, TIME_FORMAT)
            self._time_created = datetime(*tstruct[:7])
        return self._time_created

    def listen(self, listener):
        if listener not in self.listeners:
            self.listeners.append(listener)

    def unlisten(self, listener):
        self.listeners.remove(listener)

    def close(self, **kw):
        """
        This asks Tor to close the underlying circuit object. See
        :meth:`txtorcon.torstate.TorState.close_circuit`
        for details.

        You may pass keyword arguments to take care of any Flags Tor
        accepts for the CLOSECIRCUIT command. Currently, this is only
        "IfUnused". So for example: circ.close(IfUnused=True)

        :return: Deferred which callbacks with this Circuit instance
            ONLY after Tor has confirmed it is gone (not simply that the
            CLOSECIRCUIT command has been queued). This could be a while
            if you included IfUnused.
        """

        # we're already closed; nothing to do
        if self.state == 'CLOSED':
            return defer.succeed(None)

        # someone already called close() but we're not closed yet
        if self._closing_deferred:
            d = defer.Deferred()

            def closed(arg):
                d.callback(arg)
                return arg
            self._closing_deferred.addBoth(closed)
            return d

        # actually-close the circuit
        self._closing_deferred = defer.Deferred()

        def close_command_is_queued(*args):
            return self._closing_deferred
        d = self._torstate.close_circuit(self.id, **kw)
        d.addCallback(close_command_is_queued)
        return d

    def age(self, now=None):
        """
        Returns an integer which is the difference in seconds from
        'now' to when this circuit was created.

        Returns None if there is no created-time.
        """
        if not self.time_created:
            return None
        if now is None:
            now = datetime.utcnow()
        return (now - self.time_created).seconds

    def _create_flags(self, kw):
        """
        this clones the kw dict, adding a lower-case version of every
        key (duplicated in stream.py; put in util?)
        """

        flags = {}
        for k in kw.keys():
            flags[k] = kw[k]
            flags[k.lower()] = kw[k]
        return flags

    def update(self, args):
        # print "Circuit.update:",args
        if self.id is None:
            self.id = int(args[0])
            for x in self.listeners:
                x.circuit_new(self)

        else:
            if int(args[0]) != self.id:
                raise RuntimeError("Update for wrong circuit.")
        self.state = args[1]

        kw = find_keywords(args)
        self.flags = kw
        if 'PURPOSE' in kw:
            self.purpose = kw['PURPOSE']
        if 'BUILD_FLAGS' in kw:
            self.build_flags = kw['BUILD_FLAGS'].split(',')

        if self.state == 'LAUNCHED':
            self.path = []
            for x in self.listeners:
                x.circuit_launched(self)
        else:
            if self.state != 'FAILED' and self.state != 'CLOSED':
                if len(args) > 2:
                    self.update_path(args[2].split(','))

        if self.state == 'BUILT':
            for x in self.listeners:
                x.circuit_built(self)
            self._when_built.fire(self)

        elif self.state == 'CLOSED':
            if len(self.streams) > 0:
                # it seems this can/does happen if a remote router
                # crashes or otherwise shuts down a circuit with
                # streams on it still .. also if e.g. you "carml circ
                # --delete " the circuit while the stream is
                # in-progress...can we do better than logging?
                # *should* we do anything else (the stream should get
                # closed still by Tor).
                log.msg(
                    "Circuit is {} but still has {} streams".format(
                        self.state, len(self.streams)
                    )
                )
            flags = self._create_flags(kw)
            self.maybe_call_closing_deferred()
            for x in self.listeners:
                x.circuit_closed(self, **flags)

        elif self.state == 'FAILED':
            if len(self.streams) > 0:
                log.err(RuntimeError("Circuit is %s but still has %d streams" %
                                     (self.state, len(self.streams))))
            flags = self._create_flags(kw)
            self.maybe_call_closing_deferred()
            for x in self.listeners:
                x.circuit_failed(self, **flags)

    def maybe_call_closing_deferred(self):
        """
        Used internally to callback on the _closing_deferred if it
        exists.
        """

        if self._closing_deferred:
            self._closing_deferred.callback(self)
            self._closing_deferred = None
        self._when_closed.fire(self)

    def update_path(self, path):
        """
        There are EXTENDED messages which don't include any routers at
        all, and any of the EXTENDED messages may have some arbitrary
        flags in them. So far, they're all upper-case and none start
        with $ luckily. The routers in the path should all be
        LongName-style router names (this depends on them starting
        with $).

        For further complication, it's possible to extend a circuit to
        a router which isn't in the consensus. nickm via #tor thought
        this might happen in the case of hidden services choosing a
        rendevouz point not in the current consensus.
        """

        oldpath = self.path
        self.path = []
        for p in path:
            if p[0] != '$':
                break

            # this will create a Router if we give it a router
            # LongName that doesn't yet exist
            router = self.router_container.router_from_id(p)

            self.path.append(router)
            # if the path grew, notify listeners
            if len(self.path) > len(oldpath):
                for x in self.listeners:
                    x.circuit_extend(self, router)
                oldpath = self.path

    def __str__(self):
        path = ' '.join([x.ip for x in self.path])
        return "<Circuit %d %s [%s] for %s>" % (self.id, self.state, path,
                                                self.purpose)


class CircuitBuildTimedOutError(Exception):
    """
    This exception is thrown when using `timed_circuit_build`
    and the circuit build times-out.
    """


def build_timeout_circuit(tor_state, reactor, path, timeout, using_guards=False):
    """
    Build a new circuit within a timeout.

    CircuitBuildTimedOutError will be raised unless we receive a
    circuit build result (success or failure) within the `timeout`
    duration.

    :returns: a Deferred which fires when the circuit build succeeds (or
        fails to build).
    """
    timed_circuit = []
    d = tor_state.build_circuit(routers=path, using_guards=using_guards)

    def get_circuit(c):
        timed_circuit.append(c)
        return c

    def trap_cancel(f):
        f.trap(defer.CancelledError)
        if timed_circuit:
            d2 = timed_circuit[0].close()
        else:
            d2 = defer.succeed(None)
        d2.addCallback(lambda _: Failure(CircuitBuildTimedOutError("circuit build timed out")))
        return d2

    d.addCallback(get_circuit)
    d.addCallback(lambda circ: circ.when_built())
    d.addErrback(trap_cancel)

    reactor.callLater(timeout, d.cancel)
    return d
