#!/usr/bin/env python

# This shows how to get the detailed information about a
# relay descriptor and parse it into Stem's RelayDescriptor
# class. More about the class can be read from
#
# https://stem.torproject.org/api/descriptor/server_descriptor.html#stem.descriptor.server_descriptor.RelayDescriptor
#
# We need to pass the nickname or the fingerprint of the onion router
# for which we need the the descriptor information.
#
# Also you need to configure Tor to actually download these
# descriptors -- by default Tor only downloads "microdescriptors"
# (whose information is already available live via txtorcon.Router
# instances). Set "UseMicrodescriptors 0" to download "full" descriptors
from __future__ import print_function

from twisted.internet.task import react
from twisted.internet.defer import inlineCallbacks
import txtorcon

try:
    from stem.descriptor.server_descriptor import RelayDescriptor
except ImportError:
    print("You must install 'stem' to use this example:")
    print("  pip install stem")
    raise SystemExit(1)


@react
@inlineCallbacks
def main(reactor):
    tor = yield txtorcon.connect(reactor)

    or_nickname = "moria1"
    print("Trying to get decriptor information about '{}'".format(or_nickname))
    # If the fingerprint is used in place of nickname then, desc/id/<OR identity>
    # should be used.
    try:
        descriptor_info = yield tor.protocol.get_info('desc/name/' + or_nickname)
    except txtorcon.TorProtocolError:
        print("No information found. Enable descriptor downloading by setting:")
        print("  UseMicrodescritors 0")
        print("In your torrc")
        raise SystemExit(1)

    descriptor_info = descriptor_info.values()[0]
    relay_info = RelayDescriptor(descriptor_info)
    print("The relay's fingerprint is: {}".format(relay_info.fingerprint))
    print("Time in UTC when the descriptor was made: {}".format(relay_info.published))
