from __future__ import print_function

# Here we set up a Twisted Web server and then launch our own tor with
# a configured hidden service directed at the Web server we set
# up. This uses serverFromString to translate the "onion" endpoint
# descriptor into a TCPHiddenServiceEndpoint object...

from twisted.web import server, resource
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import react, deferLater
from twisted.internet.endpoints import serverFromString

import txtorcon


class Simple(resource.Resource):
    """
    A really simple Web site.
    """
    isLeaf = True

    def render_GET(self, request):
        return "<html>Hello, world! I'm a hidden service!</html>"


@react
@inlineCallbacks
def main(reactor):
    # several ways to proceed here and what they mean:
    #
    # "onion:80":
    #    launch a new Tor instance, configure a hidden service on some
    #    port and pubish descriptor for port 80
    #
    # "onion:80:controlPort=9051:localPort=8080:socksPort=9089:hiddenServiceDir=/home/human/src/txtorcon/hidserv":
    #    connect to existing Tor via control-port 9051, configure a hidden
    #    service listening locally on 8080, publish a descriptor for port
    #    80 and use an explicit hiddenServiceDir (where "hostname" and
    #    "private_key" files are put by Tor). We set SOCKS port
    #    explicitly, too.
    #
    # "onion:80:localPort=8080:socksPort=9089:hiddenServiceDir=/home/human/src/txtorcon/hidserv":
    #    all the same as above, except we launch a new Tor (because no
    #    "controlPort=9051")

    ep = "onion:80:controlPort=9051:localPort=8080:socksPort=9089:hiddenServiceDir=/home/human/src/txtorcon/hidserv"
    ep = "onion:80:localPort=8080:socksPort=9089:hiddenServiceDir=/home/human/src/txtorcon/hidserv"
    ep = "onion:80"
    hs_endpoint = serverFromString(reactor, ep)

    def progress(percent, tag, message):
        bar = int(percent / 10)
        print("[{}{}] {}".format("#" * bar, "." * (10 - bar), message))
    txtorcon.IProgressProvider(hs_endpoint).add_progress_listener(progress)

    # create our Web server and listen on the endpoint; this does the
    # actual launching of (or connecting to) tor.
    site = server.Site(Simple())
    port = yield hs_endpoint.listen(site)
    # XXX new accessor in newer API
    hs = port.onion_service

    # "port" is an IAddress implementor, in this case TorOnionAddress
    # so you can get most useful information from it -- but you can
    # also access .onion_service (see below)
    print(
        "I have set up a hidden service, advertised at:\n"
        "http://{host}:{port}\n"
        "locally listening on {local_address}\n"
        "Will stop in 60 seconds...".format(
            host=port.getHost().onion_uri,  # or hs.hostname
            port=port.public_port,
            # port.local_address will be a twisted.internet.tcp.Port
            # or a twisted.internet.unix.Port -- both have .getHost()
            local_address=port.local_address.getHost(),
        )
    )

    # if you prefer, hs (port.onion_service) is an instance providing
    # IOnionService (there's no way to do authenticated services via
    # endpoints yet, but if there was then this would implement
    # IOnionClients instead)
    print("private key:\n{}".format(hs.private_key))

    def sleep(s):
        return deferLater(reactor, s, lambda: None)

    yield sleep(50)
    for i in range(10):
        print("Stopping in {}...".format(10 - i))
        yield sleep(1)
