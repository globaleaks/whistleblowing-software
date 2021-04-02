#!/usr/bin/env python

from __future__ import print_function

from twisted.internet import task, defer
from twisted.internet.endpoints import UNIXClientEndpoint
import txtorcon


def await_single_event(tor_protocol, event_name):
    d0 = defer.Deferred()

    def _got(consensus):
        d1 = tor_protocol.remove_event_listener('NEWCONSENSUS', _got)
        d1.addCallback(lambda _: d0.callback(consensus))
        return d1
    tor_protocol.add_event_listener('NEWCONSENSUS', _got)
    return d0


@task.react
@defer.inlineCallbacks
def main(reactor):
    ep = UNIXClientEndpoint(reactor, '/var/run/tor/control')
    tor = yield txtorcon.connect(reactor, ep)

    print("waiting for next NEWCONSENSUS")
    consensus = yield await_single_event(tor.protocol, 'NEWCONSENSUS')
    print("Got NEWCONSENSUS; {} bytes".format(len(consensus)))
