#!/usr/bin/env python

# Just listens for a few EVENTs from Tor (INFO NOTICE WARN ERR) and
# prints out the contents, so functions like a log monitor.

from __future__ import print_function

from twisted.internet import task, defer
from twisted.internet.endpoints import UNIXClientEndpoint
import txtorcon


@task.react
@defer.inlineCallbacks
def main(reactor):
    ep = UNIXClientEndpoint(reactor, '/var/run/tor/control')
    tor = yield txtorcon.connect(reactor, ep)

    def log(msg):
        print(msg)
    print("Connected to a Tor version", tor.protocol.version)
    for event in ['INFO', 'NOTICE', 'WARN', 'ERR']:
        tor.protocol.add_event_listener(event, log)
    is_current = yield tor.protocol.get_info('status/version/current')
    version = yield tor.protocol.get_info('version')
    print("Version '{}', is_current={}".format(version, is_current['status/version/current']))
    yield defer.Deferred()
