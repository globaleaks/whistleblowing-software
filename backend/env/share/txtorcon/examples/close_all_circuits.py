from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import UNIXClientEndpoint

import txtorcon


@react
@inlineCallbacks
def main(reactor):
    """
    Close all open streams and circuits in the Tor we connect to
    """
    control_ep = UNIXClientEndpoint(reactor, '/var/run/tor/control')
    tor = yield txtorcon.connect(reactor, control_ep)
    state = yield tor.create_state()
    print("Closing all circuits:")
    for circuit in list(state.circuits.values()):
        path = '->'.join(map(lambda r: r.id_hex, circuit.path))
        print("Circuit {} through {}".format(circuit.id, path))
        for stream in circuit.streams:
            print("  Stream {} to {}".format(stream.id, stream.target_host))
            yield stream.close()
            print("  closed")
        yield circuit.close()
        print("closed")
    yield tor.quit()
