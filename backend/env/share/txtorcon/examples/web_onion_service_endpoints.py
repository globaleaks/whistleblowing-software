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
from twisted.internet import defer, task, endpoints, error
from twisted.web import server, resource

import txtorcon
from txtorcon.util import default_control_port


class Simple(resource.Resource):
    """
    A really simple Web site.
    """
    isLeaf = True

    def render_GET(self, request):
        return b"<html>Hello, world! I'm a hidden service!</html>"


@defer.inlineCallbacks
def main(reactor):
    # "onion:" is for Tor Onion Services, and the only required
    # argument is the public port we advertise. You can pass
    # "controlPort=9051" for example, to connect to a system Tor
    # (accepts paths, too, e.g. "controlPort=/var/run/tor/control")
    # ep = endpoints.serverFromString(reactor, "onion:80:controlPort=9151")

    # to re-create a previous hidden-service, pass the private key
    # blob you retrieved earler via port.getHost().onion_key like so:
    # ep = endpoints.serverFromString(reactor, "onion:80:privateKey=<keyblob>")
    # Beware that you have to escape the ":" after RSA1024 because of
    # reasons (the endpoint syntax uses them). For this reason, you
    # can omit the "RSA1024:" part if you wish.
    # ep = endpoints.serverFromString(reactor, "onion:80")

    # this one should be "nyfnesplt3f5nvn3.onion"

    ep = endpoints.serverFromString(reactor, "onion:80:controlPort={port}:privateKey=RSA1024\\:MIICWwIBAAKBgQDml0L1Btxe1QIs88mvKvcgAEd19bUorzMndfXXBbPt2y1lTjm+vGldJRCXb/RArfCb9F2q7IWL4ScuJBiUCqpKVG2aGK8yOxw4c5WKvnLW8MRf5+jAPlR3h7idBdrVGCY/9gXf9JzWfpIhMfFidM4Xq6VpzMvignss6FB6i9zhOwIDAQABAoGAXuWjVamUKabp9UwDFYbOGypiPmZ3Pp4TpErEeNBNAzdvUEDIPPnXNtEZKemWEMREwDnqDny2XSG0+SU7xDk7aQGTFxipo+NAl18QMW2XcBjWrIG5P0L9E+j58k5Nq6EEaMQ8G8X3hsnX7EwRqnJYOwUWUQ4emi6TvNScSMS251kCQQD6KJXltkSfwU3d5hOh37x3pOp4ZcpI6eKwwfgqP+1pVfOwjvXfLqLgLRf9+NtmG+cU5HRDwmf9rbJNCOE++11HAkEA6/mz/L+54NRk9tPN4vYfn969v7fz9CQndQUsTTrtArqtjg7baKts3ndagj+/itJfY6qV/OonN9XdntQXTWWGbQJAY244TmrJEfqieZ2WlhO49JFPRPWolpyoJvuiKSDpu6GXT8ky/zepM5OY4rDEe+yBR/OaJsihztn4cdgit4bvxwJAFsnZiOoXEFBSo8eWlXmBWlYPawlfxM8NBG8IdTjglKfkhNiIddZAQEe0dOmlHMnuLljV/UO7n9fGfEUtLutEDQJAC3c9gSe2of41TaZhQ+aHzQ8E9cs7fg3gXXUgWlocQK6fYq+tC0CF7dDmydShF8vI8oEcgJGhgtUAXQDwH9eD0A==".format(port=default_control_port()))

    def on_progress(percent, tag, msg):
        print('%03d: %s' % (percent, msg))
    txtorcon.IProgressProvider(ep).add_progress_listener(on_progress)

    try:
        port = yield ep.listen(server.Site(Simple()))
    except error.ConnectionRefusedError:
        print("Couldn't connect; is Tor listening on localhost:{}?".format(default_control_port()))
        defer.returnValue(1)

    print("Site listening: {}".format(port.getHost()))
    print("Private key:\n{}".format(port.getHost().onion_key))
    yield defer.Deferred()  # wait forever


task.react(main)
