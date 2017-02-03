from twisted.internet import reactor, protocol, defer


class ProxyClientProtocol(protocol.Protocol):
    factory = None # attached on initialization by ProxyClientFactory

    def connectionMade(self):
        self.cli_queue = self.factory.cli_queue
        self.cli_queue.get().addCallback(self.serverDataReceived)

    def serverDataReceived(self, chunk):
        if chunk is False:
            self.cli_queue = None
            self.transport.loseConnection()
        elif self.cli_queue:
            self.transport.write(chunk)
            self.cli_queue.get().addCallback(self.serverDataReceived)
        else:
            self.factory.cli_queue.put(chunk)

    def dataReceived(self, chunk):
        self.factory.srv_queue.put(chunk)

    def connectionLost(self, why):
        if self.cli_queue:
            self.cli_queue = None


class ProxyClientFactory(protocol.ClientFactory):
    protocol = ProxyClientProtocol

    def __init__(self, srv_queue, cli_queue):
        self.srv_queue = srv_queue
        self.cli_queue = cli_queue


class ProxyServerProtocol(protocol.Protocol):
    factory = None # attached on initialization by ProxyServerFactory

    def connectionMade(self):
        if self.factory.conns_have_limit:
            self.factory.conns_opened += 1

            if self.factory.conns_opened > self.factory.conns_limit:
                reactor.stop() #TODO(evilaliv3) was an exception. Now ignored.

        self.srv_queue = defer.DeferredQueue()
        self.cli_queue = defer.DeferredQueue()

        self.srv_queue.get().addCallback(self.clientDataReceived)

        cli_fact = ProxyClientFactory(self.srv_queue, self.cli_queue)
        reactor.connectTCP(self.factory.ip, self.factory.port, cli_fact)

    def clientDataReceived(self, chunk):
        self.transport.write(chunk)
        self.srv_queue.get().addCallback(self.clientDataReceived)

    def dataReceived(self, chunk):
        self.cli_queue.put(chunk)

    def connectionLost(self, reason):
        if self.factory.conns_have_limit:
            self.factory.conns_finished += 1

            if self.factory.conns_finished > self.factory.conns_limit:
                # TODO(evilaliv3) This is not a good way to stop the reactor . . . should
                # be logged
                reactor.stop()


class ProxyServerFactory(protocol.Factory):
    protocol = ProxyServerProtocol

    def __init__(self, ip, port, conns_to_serve=-1):
        self.ip = ip
        self.port = port

        # Factory state
        self.conns_have_limit = conns_to_serve > -1
        self.conns_limit = conns_to_serve
        self.conns_opened = 0
        self.conns_finished = 0
