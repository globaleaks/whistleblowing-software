from __future__ import print_function

"""
Use the 'global_tor' instance from txtorcon; this is a Tor
instance that either doesn't exist or is unique to this process'
txtorcon library (i.e. a singleton for this process)
"""

import sys
import txtorcon
import tempfile
import shutil
from os import mkdir, chmod
from os.path import join
from twisted.web.client import readBody
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks


@react
@inlineCallbacks
def main(reactor):
    # we must have a directory owned by us with 0700 permissions to
    # contain our Unix sockets or Tor is sad.
    tmp = tempfile.mkdtemp()
    reactor.addSystemEventTrigger(
        'after', 'shutdown',
        shutil.rmtree, tmp,
    )

    control_path = join(tmp, 'control_socket')
    socks_path = join(tmp, 'socks')
    # note that you can pass a few options as kwargs
    # (e.g. data_directory=, or socks_port= ). For other torrc
    # changes, see below.
    tor = yield txtorcon.launch(
        reactor,
        data_directory="./tordata",
        stdout=sys.stdout,
        control_port='unix:{}'.format(control_path),
        socks_port='unix:{}'.format(socks_path),
    )
    print("Connected to Tor version '{}'".format(tor.protocol.version))

    state = yield tor.create_state()

    print("This Tor has PID {}".format(state.tor_pid))
    print("This Tor has the following {} Circuits:".format(len(state.circuits)))
    for c in state.circuits.values():
        print("  {}".format(c))

    config = yield tor.get_config()
    socks_ep = config.create_socks_endpoint(reactor, u'unix:{}'.format(socks_path))
    agent = tor.web_agent(socks_endpoint=socks_ep)
    uri = b'https://www.torproject.org'
    print("Downloading {} via Unix socket".format(uri))
    resp = yield agent.request(b'GET', uri)
    print("Response has {} bytes".format(resp.length))
    body = yield readBody(resp)
    print("received body ({} bytes)".format(len(body)))
    print("{}\n[...]\n{}\n".format(body[:200], body[-200:]))
