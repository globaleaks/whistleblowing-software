#!/usr/bin/env python

from __future__ import print_function
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import TCP4ClientEndpoint
import txtorcon


@react
@inlineCallbacks
def main(reactor):
    ep = TCP4ClientEndpoint(reactor, "localhost", 9051)
    # or (e.g. on Debian):
    # ep = UNIXClientEndpoint(reactor, "/var/run/tor/control")
    tor = yield txtorcon.connect(reactor, ep)
    print("Connected to Tor {version}".format(version=tor.protocol.version))

    state = yield tor.create_state()
    # or:
    # state = yield txtorcon.TorState.from_protocol(tor.protocol)
    print("Tor state created. Circuits:")
    for circuit in state.circuits.values():
        print("  {circuit.id}: {circuit.path}".format(circuit=circuit))
