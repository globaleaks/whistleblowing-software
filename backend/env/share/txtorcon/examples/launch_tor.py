from __future__ import print_function

"""
Launch a private Tor instance.
"""

import sys
import txtorcon
from twisted.web.client import readBody
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks


@react
@inlineCallbacks
def main(reactor):
    # note that you can pass a few options as kwargs
    # (e.g. data_directory=, or socks_port= ). For other torrc
    # changes, see below.
    tor = yield txtorcon.launch(
        reactor,
        data_directory="./tordata",
        stdout=sys.stdout,
        socks_port='unix:/tmp/tor2/socks',
    )
    # tor = yield txtorcon.connect(
    #     reactor,
    #     clientFromString(reactor, "unix:/var/run/tor/control"),
    # )
    print("Connected to Tor version '{}'".format(tor.protocol.version))

    config = yield tor.get_config()
    state = yield tor.create_state()
    # or state = yield txtorcon.TorState.from_protocol(tor.protocol)

    print("This Tor has PID {}".format(state.tor_pid))
    print("This Tor has the following {} Circuits:".format(len(state.circuits)))
    for c in state.circuits.values():
        print("  {}".format(c))

    endpoint_d = config.socks_endpoint(reactor, u'unix:/tmp/tor2/socks')
    agent = tor.web_agent(socks_endpoint=endpoint_d)
    uri = b'https://www.torproject.org'
    print("Downloading {}".format(uri))
    resp = yield agent.request(b'GET', uri)
    print("Response has {} bytes".format(resp.length))
    body = yield readBody(resp)
    print("received body ({} bytes)".format(len(body)))
    print("{}\n[...]\n{}\n".format(body[:200], body[-200:]))

    # SOCKSPort is 'really' a list of SOCKS ports in Tor now, so we
    # have to set it to a list ... :/
    print("Changing our config (SOCKSPort=9876)")
    # config.SOCKSPort = ['unix:/tmp/foo/bar']
    config.SOCKSPort = ['9876']
    yield config.save()

    print("Querying to see it changed:")
    socksport = yield tor.protocol.get_conf("SOCKSPort")
    print("SOCKSPort", socksport)
