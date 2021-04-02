# this example shows how to use specific circuits over Tor (with
# Twisted's web client or with a custom protocol)
#
# NOTE WELL: this functionality is for advanced use-cases and if you
# do anything "special" to select your circuit hops you risk making it
# easy to de-anonymize this (and all other) Tor circuits.

from __future__ import print_function

from twisted.internet.protocol import Protocol, Factory
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet.task import react
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.client import readBody

import txtorcon
from txtorcon.util import default_control_port


@react
@inlineCallbacks
def main(reactor):
    # use port 9051 for system tor instances, or:
    # ep = UNIXClientEndpoint(reactor, '/var/run/tor/control')
    ep = TCP4ClientEndpoint(reactor, '127.0.0.1', default_control_port())
    tor = yield txtorcon.connect(reactor, ep)
    print("Connected:", tor)

    config = yield tor.get_config()
    state = yield tor.create_state()
    socks = config.socks_endpoint(reactor)

    # create a custom circuit; in this case we're just letting Tor
    # decide the path but you *can* select a path (again: for advanced
    # use cases that will probably de-anonymize you)
    circ = yield state.build_circuit()
    print("Building a circuit:", circ)

    # at this point, the circuit will be "under way" but may not yet
    # be in BUILT state -- and hence usable. So, we wait. (Just for
    # demo purposes: the underlying connect will wait too)
    yield circ.when_built()
    print("Circuit is ready:", circ)

    if True:
        # create a web.Agent that will use this circuit (or fail)
        agent = circ.web_agent(reactor, socks)

        uri = 'https://www.torproject.org'
        print("Downloading {}".format(uri))
        resp = yield agent.request('GET', uri)

        print("Response has {} bytes".format(resp.length))
        body = yield readBody(resp)
        print("received body ({} bytes)".format(len(body)))
        print("{}\n[...]\n{}\n".format(body[:200], body[-200:]))

    if True:
        # make a plain TCP connection to a thing
        ep = circ.stream_via(reactor, 'torproject.org', 80, config.socks_endpoint(reactor))

        d = Deferred()

        class ToyWebRequestProtocol(Protocol):

            def connectionMade(self):
                print("Connected via {}".format(self.transport.getHost()))
                self.transport.write(
                    'GET http://torproject.org/ HTTP/1.1\r\n'
                    'Host: torproject.org\r\n'
                    '\r\n'
                )

            def dataReceived(self, d):
                print("  received {} bytes".format(len(d)))

            def connectionLost(self, reason):
                print("disconnected: {}".format(reason.value))
                d.callback(None)

        proto = yield ep.connect(Factory.forProtocol(ToyWebRequestProtocol))
        yield d
        print("All done, closing the circuit")
        yield circ.close()
