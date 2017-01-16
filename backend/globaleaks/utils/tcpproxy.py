from twisted.internet import reactor, protocol, defer


class ProxyClientProtocol(protocol.Protocol):
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
    def connectionMade(self):
        if self.factory.connectionState is not None:
            self.factory.connectionState['counter'] += 1

            if self.factory.connectionState['counter'] >= self.factory.connectionState['connectionsLimit']:
                port.stopListening()

        self.srv_queue = defer.DeferredQueue()
        self.cli_queue = defer.DeferredQueue()

        self.srv_queue.get().addCallback(self.clientDataReceived)

        factory = ProxyClientFactory(self.srv_queue, self.cli_queue)
        reactor.connectTCP(self.factory.ip, self.factory.port, factory)

    def clientDataReceived(self, chunk):
        self.transport.write(chunk)
        self.srv_queue.get().addCallback(self.clientDataReceived)

    def dataReceived(self, chunk):
        self.cli_queue.put(chunk)

    def connectionLost(self, reason):
        if self.factory.connectionState is not None:
            self.factory.connectionState['counter'] -= 1
            self.factory.connectionState['countdown'] -= 1

            if self.factory.connectionState['countdown'] <= 0:
                reactor.stop()


class ProxyServerFactory(protocol.Factory):
    protocol = ProxyServerProtocol
    connectionState = None

    def __init__(self, ip, port, connectionsLimit=-1):
        self.ip = ip
        self.port = port

        if connectionsLimit > 0:
            self.connectionState = {
              'counter': 0,
              'countdown': connectionsLimit,
              'connectionsLimit': connectionsLimit
            }
