# -*- coding: utf-8 -*-

"""
Contains an implementation of a :class:`Stream abstraction used by
:class:`TorState to represent all streams in Tor's state. There is
also an interface called :class:`interface.IStreamListener` for
listening for stream updates (see also
:meth:`TorState.add_stream_listener`) and the interface called
:class:interface.IStreamAttacher` used by :class:`TorState` as a way
to attach streams to circuits "by hand"

"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import with_statement

from twisted.python import log
from twisted.internet import defer
from txtorcon.interface import ICircuitContainer, IStreamListener
from txtorcon.util import find_keywords, maybe_ip_addr


class Stream(object):
    """
    Represents an active stream in Tor's state (:class:`txtorcon.TorState`).

    :ivar circuit:
        Streams will generally be attached to circuits pretty
        quickly. If they are attached, circuit will be a
        :class:`txtorcon.Circuit` instance or None if this stream
        isn't yet attached to a circuit.

    :ivar state:
        Tor's idea of the stream's state, one of:
          - NEW: New request to connect
          - NEWRESOLVE: New request to resolve an address
          - REMAP: Address re-mapped to another
          - SENTCONNECT: Sent a connect cell along a circuit
          - SENTRESOLVE: Sent a resolve cell along a circuit
          - SUCCEEDED: Received a reply; stream established
          - FAILED: Stream failed and not retriable
          - CLOSED: Stream closed
          - DETACHED: Detached from circuit; still retriable

    :ivar target_host:
        Something like www.example.com -- the host the stream is destined for.

    :ivar target_port:
        The port the stream will exit to.

    :ivar target_addr:
        Target address, looked up (usually) by Tor (e.g. 127.0.0.1).

    :ivar id:
        The ID of this stream, a number (or None if unset).
    """

    def __init__(self, circuitcontainer, addrmap=None):
        """
        :param circuitcontainer: an object which implements
            :class:`interface.ICircuitContainer`
        """

        self.circuit_container = ICircuitContainer(circuitcontainer)

        # FIXME: Sphinx doesn't seem to understand these variable
        # docstrings, so consolidate with above if Sphinx is the
        # answer -- actually it does, so long as the :ivar: things
        # are never mentioned it seems.

        self.id = None
        """An int, Tor's ID for this :class:`txtorcon.Circuit`"""

        self.state = None
        """A string, Tor's idea of the state of this
        :class:`txtorcon.Stream`"""

        self.target_host = None
        """Usually a hostname, but sometimes an IP address (e.g. when
        we query existing state from Tor)"""

        self.target_addr = None
        """If available, the IP address we're connecting to (if None,
        see target_host instead)."""

        self.target_port = 0
        """The port we're connecting to."""

        self.circuit = None
        """If we've attached to a :class:`txtorcon.Circuit`, this will
        be an instance of :class:`txtorcon.Circuit` (otherwise None)."""

        self.listeners = []
        """A list of all connected
        :class:`txtorcon.interface.IStreamListener` instances."""

        self.source_addr = None
        """If available, the address from which this Stream originated
        (e.g. local process, etc). See get_process() also."""

        self.source_port = 0
        """If available, the port from which this Stream
        originated. See get_process() also."""

        self.flags = {}
        """All flags from last update to this Stream. str->str"""

        self._closing_deferred = None
        """Internal. Holds Deferred that will callback when this
        stream is CLOSED, FAILED (or DETACHED??)"""

        self._addrmap = addrmap

    def listen(self, listen):
        """
        Attach an :class:`txtorcon.interface.IStreamListener` to this stream.

        See also :meth:`txtorcon.TorState.add_stream_listener` to
        listen to all streams.

        :param listen: something that knows
            :class:`txtorcon.interface.IStreamListener`
        """

        listener = IStreamListener(listen)
        if listener not in self.listeners:
            self.listeners.append(listener)

    def unlisten(self, listener):
        self.listeners.remove(listener)

    def close(self, **kw):
        """
        This asks Tor to close the underlying stream object. See
        :meth:`txtorcon.interface.ITorControlProtocol.close_stream`
        for details.

        Although Tor currently takes no flags, it allows you to; any
        keyword arguments are passed through as flags.

        NOTE that the callback delivered from this method only
        callbacks after the underlying stream is really destroyed
        (*not* just when the CLOSESTREAM command has successfully
        completed).
        """

        self._closing_deferred = defer.Deferred()

        def close_command_is_queued(*args):
            return self._closing_deferred
        d = self.circuit_container.close_stream(self, **kw)
        d.addCallback(close_command_is_queued)
        return self._closing_deferred

    def _create_flags(self, kw):
        """
        this clones the kw dict, adding a lower-case version of every key
        (duplicated in circuit.py; consider putting in util?)
        """

        flags = {}
        for k in kw.keys():
            flags[k] = kw[k]
            flags[k.lower()] = flags[k]
        return flags

    def update(self, args):
        if self.id is None:
            self.id = int(args[0])
        else:
            if self.id != int(args[0]):
                raise RuntimeError("Update for wrong stream.")

        kw = find_keywords(args)
        self.flags = kw

        if 'SOURCE_ADDR' in kw:
            last_colon = kw['SOURCE_ADDR'].rfind(':')
            self.source_addr = kw['SOURCE_ADDR'][:last_colon]
            if self.source_addr != '(Tor_internal)':
                self.source_addr = maybe_ip_addr(self.source_addr)
            self.source_port = int(kw['SOURCE_ADDR'][last_colon + 1:])

        self.state = args[1]
        # XXX why not using the state-machine stuff? ;)
        if self.state in ['NEW', 'NEWRESOLVE', 'SUCCEEDED']:
            if self.target_host is None:
                last_colon = args[3].rfind(':')
                self.target_host = args[3][:last_colon]
                self.target_port = int(args[3][last_colon + 1:])
                # target_host is often an IP address (newer tors? did
                # this change?) so we attempt to look it up in our
                # AddrMap and make it a name no matter what.
                if self._addrmap:
                    try:
                        h = self._addrmap.find(self.target_host)
                        self.target_host = h.name
                    except KeyError:
                        pass

            self.target_port = int(self.target_port)
            if self.state == 'NEW':
                if self.circuit is not None:
                    log.err(RuntimeError("Weird: circuit valid in NEW"))
                self._notify('stream_new', self)
            else:
                self._notify('stream_succeeded', self)

        elif self.state == 'REMAP':
            self.target_addr = maybe_ip_addr(args[3][:args[3].rfind(':')])

        elif self.state == 'CLOSED':
            if self.circuit:
                self.circuit.streams.remove(self)
            self.circuit = None
            self.maybe_call_closing_deferred()
            flags = self._create_flags(kw)
            self._notify('stream_closed', self, **flags)

        elif self.state == 'FAILED':
            if self.circuit:
                self.circuit.streams.remove(self)
            self.circuit = None
            self.maybe_call_closing_deferred()
            # build lower-case version of all flags
            flags = self._create_flags(kw)
            self._notify('stream_failed', self, **flags)

        elif self.state == 'SENTCONNECT':
            pass  # print 'SENTCONNECT',self,args

        elif self.state == 'DETACHED':
            if self.circuit:
                self.circuit.streams.remove(self)
                self.circuit = None

            # FIXME does this count as closed?
            # self.maybe_call_closing_deferred()
            flags = self._create_flags(kw)
            self._notify('stream_detach', self, **flags)

        elif self.state in ['NEWRESOLVE', 'SENTRESOLVE']:
            pass  # print self.state, self, args

        else:
            raise RuntimeError("Unknown state: %s" % self.state)

        # see if we attached to a circuit. I believe this only happens
        # on a SENTCONNECT or REMAP. DETACHED is excluded so we don't
        # immediately re-add the circuit we just detached from
        if self.state not in ['CLOSED', 'FAILED', 'DETACHED']:
            cid = int(args[2])
            if cid == 0:
                if self.circuit and self in self.circuit.streams:
                    self.circuit.streams.remove(self)
                self.circuit = None

            else:
                if self.circuit is None:
                    self.circuit = self.circuit_container.find_circuit(cid)
                    if self not in self.circuit.streams:
                        self.circuit.streams.append(self)
                        self._notify('stream_attach', self, self.circuit)

                else:
                    # XXX I am seeing this from torexitscan (*and*
                    # from my TorNS thing, so I think it's some kind
                    # of 'consistent' behavior out of Tor) so ... this
                    # is probably when we're doing stream-attachment
                    # stuff? maybe the stream gets assigned a circuit
                    # 'provisionally' and then it's changed?
                    # ...yup, looks like it!
                    if self.circuit.id != cid:
                        # you can get SENTCONNECT twice in a row (for example) with different circuit-ids if there is something (e.g. another txtorcon) doing R
                        log.err(
                            RuntimeError(
                                'Circuit ID changed from %d to %d state=%s.' %
                                (self.circuit.id, cid, self.state)
                            )
                        )

    def _notify(self, func, *args, **kw):
        """
        Internal helper. Calls the IStreamListener function 'func' with
        the given args, guarding around errors.
        """
        for x in self.listeners:
            try:
                getattr(x, func)(*args, **kw)
            except Exception:
                log.err()

    def maybe_call_closing_deferred(self):
        """
        Used internally to callback on the _closing_deferred if it
        exists.
        """

        if self._closing_deferred:
            self._closing_deferred.callback(self)
            self._closing_deferred = None

    def __str__(self):
        c = ''
        if self.circuit:
            c = 'on %d ' % self.circuit.id
        return "<Stream %s %d %s%s -> %s port %d>" % (self.state,
                                                      self.id,
                                                      c,
                                                      self.target_host,
                                                      str(self.target_addr),
                                                      self.target_port)
