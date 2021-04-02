#!/usr/bin/env python

# This uses an IStreamListener and an ICircuitListener to log all
# built circuits and all streams that succeed.

from __future__ import print_function

import sys
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks, Deferred
import txtorcon


def log_circuit(circuit):
    path = '->'.join(map(lambda x: str(x.location.countrycode), circuit.path))
    log.msg('Circuit %d (%s) is %s for purpose "%s"' %
            (circuit.id, path, circuit.state, circuit.purpose))


def log_stream(stream):
    circ = ''
    if stream.circuit:
        path = '->'.join(map(lambda x: str(x.location.countrycode), stream.circuit.path))
        circ = ' via circuit %d (%s)' % (stream.circuit.id, path)
    proc = txtorcon.util.process_from_address(
        stream.source_addr,
        stream.source_port,
    )
    if proc:
        proc = ' from process "%s"' % (proc, )

    elif stream.source_addr == '(Tor_internal)':
        proc = ' for Tor internal use'

    else:
        proc = ' from remote "%s:%s"' % (str(stream.source_addr),
                                         str(stream.source_port))
    log.msg('Stream %d to %s:%d attached%s%s' %
            (stream.id, stream.target_host, stream.target_port, circ, proc))


class StreamCircuitLogger(txtorcon.StreamListenerMixin,
                          txtorcon.CircuitListenerMixin):

    def stream_attach(self, stream, circuit):
        log_stream(stream)

    def stream_failed(self, stream, reason='', remote_reason='', **kw):
        print('Stream %d failed because "%s"' % (stream.id, remote_reason))

    def circuit_built(self, circuit):
        log_circuit(circuit)

    def circuit_failed(self, circuit, **kw):
        log.msg('Circuit %d failed "%s"' % (circuit.id, kw['REASON']))


@react
@inlineCallbacks
def main(reactor):
    log.startLogging(sys.stdout)

    tor = yield txtorcon.connect(reactor)
    log.msg('Connected to a Tor version %s' % tor.protocol.version)
    state = yield tor.create_state()

    listener = StreamCircuitLogger()
    state.add_circuit_listener(listener)
    state.add_stream_listener(listener)

    tor.protocol.add_event_listener('STATUS_GENERAL', log.msg)
    tor.protocol.add_event_listener('STATUS_SERVER', log.msg)
    tor.protocol.add_event_listener('STATUS_CLIENT', log.msg)

    log.msg('Existing state when we connected:')
    for s in state.streams.values():
        log_stream(s)

    log.msg('Existing circuits:')
    for c in state.circuits.values():
        log_circuit(c)
    yield Deferred()
