from __future__ import print_function
from twisted.internet import protocol, reactor, endpoints

# like the echo-server example on the front page of
# https://twistedmatrix.com except this makes a Tor onion-service
# that's an echo server.
#
# Note the *only* difference is the string we give to "serverFromString"!


class Echo(protocol.Protocol):
    def connectionMade(self):
        print("Connection from {}".format(self.transport.getHost()))

    def dataReceived(self, data):
        print("echoing: '{}'".format(repr(data)))
        self.transport.write(data)


class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()


print("Starting Tor, and onion service (can take a few minutes)")
d = endpoints.serverFromString(reactor, "onion:1234").listen(EchoFactory())


def listening(port):
    # port is a Twisted IListeningPort
    print("Listening on: {} port 1234".format(port.getHost()))
    print("Try: torsocks telnet {} 1234".format(port.getHost().onion_uri))


d.addCallback(listening)
reactor.run()
