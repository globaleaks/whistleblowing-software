# this is a Python3 version of the code in readme.py

from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks, ensureDeferred
from twisted.internet.endpoints import UNIXClientEndpoint

import treq
import txtorcon


async def main(reactor):
    tor = await txtorcon.connect(
        reactor,
        UNIXClientEndpoint(reactor, "/var/run/tor/control")
    )

    print("Connected to Tor version {}".format(tor.version))

    url = u'https://www.torproject.org:443'
    print(u"Downloading {}".format(repr(url)))
    resp = await treq.get(url, agent=tor.web_agent())

    print(u"   {} bytes".format(resp.length))
    data = await resp.text()
    print(u"Got {} bytes:\n{}\n[...]{}".format(
        len(data),
        data[:120],
        data[-120:],
    ))

    print(u"Creating a circuit")
    state = await tor.create_state()
    circ = await state.build_circuit()
    await circ.when_built()
    print(u"  path: {}".format(" -> ".join([r.ip for r in circ.path])))

    print(u"Downloading meejah's public key via above circuit...")
    config = await tor.get_config()
    resp = await treq.get(
        u'https://meejah.ca/meejah.asc',
        agent=circ.web_agent(reactor, config.socks_endpoint(reactor)),
    )
    data = await resp.text()
    print(data)


@react
def _main(reactor):
    return ensureDeferred(main(reactor))
