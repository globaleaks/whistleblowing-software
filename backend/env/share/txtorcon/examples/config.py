from __future__ import print_function

import sys
import txtorcon
from twisted.web.client import readBody
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks
from twisted.internet.endpoints import clientFromString


@react
@inlineCallbacks
def main(reactor):
    control_ep = clientFromString(reactor, "tcp:localhost:9251")
    tor = yield txtorcon.connect(reactor, control_ep)
    print("Connected to Tor version '{}'".format(tor.protocol.version))

    config = yield tor.get_config()

    print("SocksPort={}".format(config.SocksPort[0]))

    print("Directory authorities:")
    for a in config.DirAuthority:
        print("  {}".format(a[1:-1].split()[0]))
    return

    stuff = yield tor.protocol.get_info('config/defaults')
    stuff = stuff['config/defaults']
    for line in stuff.strip().split('\n'):
        k, v = line.split(' ', 1)
        if k not in ['FallbackDir']:
            v = yield tor.protocol.get_conf(k)
            print('{} = {}'.format(k, v))
            continue
            try:
                print('{} = {}'.format(k, getattr(config, k)))
            except KeyError:
                print('error on {}'.format(k))
