#!/usr/bin/env python

# This shows how to leverage the endpoints API to get a new hidden
# service up and running quickly. You can pass along this API to your
# users by accepting endpoint strings as per Twisted recommendations.
#
# http://twistedmatrix.com/documents/current/core/howto/endpoints.html#maximizing-the-return-on-your-endpoint-investment
#
# note that only the progress-updates needs the "import txtorcon" --
# you do still need it installed so that Twisted finds the endpoint
# parser plugin but code without knowledge of txtorcon can still
# launch a Tor instance using it. cool!

from __future__ import print_function
from twisted.internet import defer, task, endpoints
from twisted.web import server, resource

import txtorcon
from txtorcon.util import default_control_port
from txtorcon.onion import AuthBasic


class Simple(resource.Resource):
    """
    A really simple Web site.
    """
    isLeaf = True

    def render_GET(self, request):
        return b"<html>Hello, world! I'm a single-hop hidden service!</html>"


@defer.inlineCallbacks
def main(reactor):
    tor = yield txtorcon.connect(
        reactor,
        endpoints.TCP4ClientEndpoint(reactor, "localhost", 9251),
    )
    ep = endpoints.serverFromString(
        reactor,
        "onion:80:version=3:privateKeyFile=/home/mike/src/txtorcon/foodir/hs_ed25519_secret_key"
    )

    def on_progress(percent, tag, msg):
        print('%03d: %s' % (percent, msg))
    txtorcon.IProgressProvider(ep).add_progress_listener(on_progress)
    print("Note: descriptor upload can take several minutes")

    port = yield ep.listen(server.Site(Simple()))
    print("Private key:\n{}".format(port.getHost().onion_key))
    hs = port.onion_service
    print("hs {}".format(hs))
    print("{}".format(hs.hostname))
    yield defer.Deferred()  # wait forever


task.react(main)
