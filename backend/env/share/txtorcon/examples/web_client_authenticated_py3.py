# this example shows how to use Twisted's web client with Tor via
# txtorcon

from __future__ import print_function

from twisted.internet.defer import inlineCallbacks, ensureDeferred
from twisted.internet.task import react
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.client import readBody

import txtorcon
from txtorcon.util import default_control_port


async def main(reactor):
    # use port 9051 for system tor instances, or:
    # ep = UNIXClientEndpoint(reactor, '/var/run/tor/control')
    # ep = UNIXClientEndpoint(reactor, '/var/run/tor/control')
    ep = TCP4ClientEndpoint(reactor, '127.0.0.1', default_control_port())
    tor = await txtorcon.connect(reactor, ep)
    print("Connected to {tor} via localhost:{port}".format(
        tor=tor,
        port=default_control_port(),
    ))

    # add our client-side authentication tokens for the service.
    # You can create these by running the
    # web_onion_service_ephemeral_auth.py in a separate shell and
    # using either the "alice" or "bob" token in this client.
    token = u"0GaFhnbunp0TxZuBhejhxg"  # alice's token
    onion_uri = u"FIXME.onion"

    if u"FIXME" in onion_uri:
        print("Please edit to the correct .onion URI")
        return

    async with tor.onion_authentication(onion_uri, token):
        # do the Web request as with any other
        agent = tor.web_agent()
        uri = u'http://{}/'.format(onion_uri)
        print("Downloading {}".format(uri))
        resp = await agent.request(b'GET', uri.encode('ascii'))

        print("Response has {} bytes".format(resp.length))
        body = await readBody(resp)
        print(body)

if __name__ == '__main__':
    def _main(reactor):
        return ensureDeferred(main(reactor))
    react(_main)
