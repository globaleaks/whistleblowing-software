from __future__ import print_function

from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import UNIXClientEndpoint
import treq
import txtorcon


@react
@inlineCallbacks
def main(reactor):
    tor = yield txtorcon.connect(
        reactor,
        UNIXClientEndpoint(reactor, "/var/run/tor/control")
    )

    print("Connected to Tor version {}".format(tor.version))

    url = 'https://www.torproject.org:443'
    print("Downloading {}".format(url))
    resp = yield treq.get(url, agent=tor.web_agent())

    print("   {} bytes".format(resp.length))
    data = yield resp.text()
    print("Got {} bytes:\n{}\n[...]{}".format(
        len(data),
        data[:120],
        data[-120:],
    ))

    print("Creating a circuit")
    state = yield tor.create_state()
    circ = yield state.build_circuit()
    yield circ.when_built()
    print("  path: {}".format(" -> ".join([r.ip for r in circ.path])))

    print("Downloading meejah's public key via above circuit...")
    config = yield tor.get_config()
    resp = yield treq.get(
        'https://meejah.ca/meejah.asc',
        agent=circ.web_agent(reactor, config.socks_endpoint(reactor)),
    )
    data = yield resp.text()
    print(data)
