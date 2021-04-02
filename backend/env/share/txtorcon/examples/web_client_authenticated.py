# this example shows how to use Twisted's web client with Tor via
# txtorcon

from __future__ import print_function

from twisted.internet.defer import inlineCallbacks
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
    # ep = UNIXClientEndpoint(reactor, '/var/run/tor/control')
    ep = TCP4ClientEndpoint(reactor, '127.0.0.1', default_control_port())
    tor = yield txtorcon.connect(reactor, ep)
    print("Connected to {tor} via localhost:{port}".format(
        tor=tor,
        port=default_control_port(),
    ))

    # add our client-side authentication tokens for the service.
    # You can create these by running the
    # web_onion_service_ephemeral_auth.py in a separate shell and
    # using either the "alice" or "bob" token in this client.
    token = u"0GaFhnbunp0TxZuBhejhxg"  # alice's token
    onion_uri = b"FIXME.onion"

    if b'FIXME' in onion_uri:
        print("Please edit to the correct .onion URI")
        return

    yield tor.add_onion_authentication(onion_uri, token)
    try:
        # do the Web request as with any other
        agent = tor.web_agent()
        uri = b'http://{}/'.format(onion_uri)
        print("Downloading {}".format(uri))
        resp = yield agent.request(b'GET', uri)

        print("Response has {} bytes".format(resp.length))
        body = yield readBody(resp)
        print(body)
    finally:
        # if you're using python3, see the example that uses async
        # context-managers to do this more cleanly.
        yield tor.remove_onion_authentication(onion_uri)
