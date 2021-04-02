from __future__ import print_function
#
# This uses a very simple custom txtorcon.IStreamAttacher to disallow
# certain streams based solely on their port; by default it closes
# all streams on port 80 or 25 without ever attaching them to a
# circuit.
#
# For a more complex IStreamAttacher example, see
# attach_streams_by_country.py
#

from twisted.python import log
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet.endpoints import clientFromString
from zope.interface import implementer

import txtorcon


@implementer(txtorcon.IStreamAttacher)
class PortFilterAttacher:

    def __init__(self, state):
        self.state = state
        self.disallow_ports = [80, 25]
        print(
            "Disallowing all streams to ports: {ports}".format(
                ports=",".join(map(str, self.disallow_ports)),
            )
        )

    def attach_stream(self, stream, circuits):
        """
        IStreamAttacher API
        """

        def stream_closed(x):
            print("Stream closed:", x)

        if stream.target_port in self.disallow_ports:
            print(
                "Disallowing {stream} to port {stream.target_port}".format(
                    stream=stream,
                )
            )
            d = self.state.close_stream(stream)
            d.addCallback(stream_closed)
            d.addErrback(log.err)
            return txtorcon.TorState.DO_NOT_ATTACH

        # Ask Tor to assign stream to a circuit by itself
        return None


@react
@inlineCallbacks
def main(reactor):
    control_ep = clientFromString(reactor, "tcp:localhost:9051")
    tor = yield txtorcon.connect(reactor, control_ep)
    print("Connected to a Tor version={version}".format(
        version=tor.protocol.version,
    ))
    state = yield tor.create_state()
    yield state.set_attacher(PortFilterAttacher(state), reactor)

    print("Existing streams:")
    for s in state.streams.values():
        print("  ", s)
    yield Deferred()
