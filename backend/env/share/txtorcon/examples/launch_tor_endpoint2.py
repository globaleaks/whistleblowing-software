#!/usr/bin/env python

# Here we set up a Twisted Web server and then launch a slave tor
# with a configured hidden service directed at the Web server we set
# up. This uses serverFromString to translate the "onion" endpoint descriptor
# into a TCPHiddenServiceEndpoint object...

from __future__ import print_function

from twisted.internet import reactor
from twisted.web import server, resource
from twisted.internet.endpoints import serverFromString

import txtorcon


class Simple(resource.Resource):
    isLeaf = True

    def render_GET(self, request):
        return "<html>Hello, world! I'm a hidden service!</html>"


site = server.Site(Simple())


def setup_failed(arg):
    print("SETUP FAILED", arg)


def setup_complete(port):
    print("Hidden serivce:", port.getHost().onion_service)
    print("    locally at:", port.local_address)


def progress(percent, tag, message):
    bar = int(percent / 10)
    print('[%s%s] %s' % ('#' * bar, '.' * (10 - bar), message))


hs_endpoint1 = serverFromString(reactor, "onion:80")
hs_endpoint2 = serverFromString(reactor, "onion:80")

txtorcon.IProgressProvider(hs_endpoint1).add_progress_listener(progress)
txtorcon.IProgressProvider(hs_endpoint2).add_progress_listener(progress)

d1 = hs_endpoint1.listen(site)
d2 = hs_endpoint2.listen(site)

d1.addCallback(setup_complete).addErrback(setup_failed)
d2.addCallback(setup_complete).addErrback(setup_failed)

reactor.run()
