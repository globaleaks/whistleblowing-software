#!/usr/bin/env python

# launch a tor, and then connect a TorConfig object to it and
# re-configure it. This allows us to determine what features the
# running tor supports, *without* resorting to looking at version
# numbers.

from __future__ import print_function

import sys
from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks, Deferred
import txtorcon


@inlineCallbacks
def main(reactor, tor_binary):
    config = txtorcon.TorConfig()
    config.ORPort = 0
    config.SOCKSPort = 0
    config.Tor2WebMode = 1
    # leaving ControlPort unset; launch_tor will choose one

    print("Launching tor...", tor_binary)
    try:
        yield txtorcon.launch_tor(
            config,
            reactor,
            tor_binary=tor_binary,
            stdout=sys.stdout
        )
        print("success! We support Tor2Web mode")

    except RuntimeError as e:
        print("There was a problem:", str(e))
        print("We do NOT support Tor2Web mode")
        return

    print("quitting in 5 seconds")
    reactor.callLater(5, lambda: reactor.stop())
    yield Deferred()  # wait forever because we never .callback()


if __name__ == '__main__':
    tor_binary = None
    if len(sys.argv) > 1:
        tor_binary = sys.argv[1]
    # Twisted's newer task APIs are nice
    react(main, (tor_binary,))
