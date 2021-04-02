#!/usr/bin/env python

from __future__ import print_function
import os

from twisted.internet import defer, task, endpoints
from twisted.web import server, static, resource

import txtorcon


@defer.inlineCallbacks
def main(reactor):
    # a simple Web site; could be any other listening service of course
    res = resource.Resource()
    res.putChild(
        b'',
        static.Data("<html>Hello, onion-service world!</html>", 'text/html')
    )

    def on_progress(percent, tag, msg):
        print('%03d: %s' % (percent, msg))

    # We are using launch() here instead of connect() because
    # filesystem services are very picky about the permissions and
    # ownership of the directories involved. If you *do* want to
    # connect to e.g. a system service or Tor Browser Bundle, it's way
    # more likely to work to use Ephemeral services

    tor = yield txtorcon.connect(
        reactor,
        endpoints.TCP4ClientEndpoint(reactor, "localhost", txtorcon.util.default_control_port()),
    )

    # NOTE: you should put these somewhere you've thought about more
    # and made proper permissions for the parent directory, etc. A
    # good choice for a system-wide Tor is /var/lib/tor/<whatever>
    # The parent directory must be mode 700
    os.mkdir("hs_parent")
    os.chmod("hs_parent", 0o700)
    hs_dir = './hs_parent/hs_dir'

    print("Creating stealth-authenticated hidden-service, keys in: {}".format(hs_dir))
    ep = tor.create_authenticated_filesystem_onion_endpoint(
        80,
        hs_dir=hs_dir,
        auth=txtorcon.AuthStealth(['alice', 'bob']),
        group_readable=True,
    )

    print("Note: descriptor upload can take several minutes")

    txtorcon.IProgressProvider(ep).add_progress_listener(on_progress)

    port = yield ep.listen(server.Site(res))
    hs = port.getHost().onion_service
    for name in hs.client_names():
        client = hs.get_client(name)
        print("  {}: {}".format(name, client.hostname))
        print("     auth token: {}".format(client.auth_token))
        print("    private key: {}..".format(client.private_key[:40]))
        print("    HidServAuth {} {}".format(client.hostname, client.auth_token))
    yield tor.protocol.on_disconnect
    print("disconnected")


if __name__ == '__main__':
    task.react(main)
