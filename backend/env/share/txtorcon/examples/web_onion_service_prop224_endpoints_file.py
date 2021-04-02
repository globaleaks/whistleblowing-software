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


class Simple(resource.Resource):
    """
    A really simple Web site.
    """
    isLeaf = True

    def render_GET(self, request):
        return b"<html>Hello, world! I'm a prop224 Onion Service!</html>"


@defer.inlineCallbacks
def main(reactor):
    tor = yield txtorcon.connect(
        reactor,
        endpoints.TCP4ClientEndpoint(reactor, "localhost", 9251),
    )
    print(default_control_port())
    ep = tor.create_filesystem_onion_endpoint(80, "./test_prop224_service", version=3)

    def on_progress(percent, tag, msg):
        print('%03d: %s' % (percent, msg))
    txtorcon.IProgressProvider(ep).add_progress_listener(on_progress)
    print("Note: descriptor upload can take several minutes")

    port = yield ep.listen(server.Site(Simple()))
    print("Site listening: {}".format(port.getHost()))
    print("Private key:\n{}".format(port.getHost().onion_key))
    yield defer.Deferred()  # wait forever


task.react(main)
