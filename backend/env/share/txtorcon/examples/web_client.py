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

    # create a web.Agent that will talk via Tor. If the socks port
    # given isn't yet configured, this will do so. It may also be
    # None, which means "the first configured SOCKSPort"
    # agent = tor.web_agent(u'9999')
    agent = tor.web_agent()
    uri = b'http://surely-this-has-not-been-registered-and-is-invalid.com'
    uri = b'https://www.torproject.org'
    uri = b'http://timaq4ygg2iegci7.onion/'  # txtorcon documentation
    print("Downloading {}".format(uri))
    resp = yield agent.request(b'GET', uri)

    print("Response has {} bytes".format(resp.length))
    body = yield readBody(resp)
    print("received body ({} bytes)".format(len(body)))
    print("{}\n[...]\n{}\n".format(body[:200], body[-200:]))
