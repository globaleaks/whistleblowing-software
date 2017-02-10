import urlparse

from zope.interface import implements

from twisted.web import http, client, _newclient
from twisted.web.client import Agent
from twisted.internet import reactor, protocol, defer, address
from twisted.web.iweb import IBodyProducer
from twisted.web.server import NOT_DONE_YET

class BodyProducer(object):
    implements(IBodyProducer)

    def __init__(self):
        self.length = _newclient.UNKNOWN_LENGTH
        self.finished = defer.Deferred()
        self.consumer = None
        self.can_stream = False
        self.can_stream_d = defer.Deferred()

    def startProducing(self, consumer):
        self.consumer = consumer
        self.can_stream = True
        self.can_stream_d.callback(True)
        return self.finished

    @defer.inlineCallbacks
    def dataReceived(self, data):
        print("Data received called")
        if not self.can_stream:
            yield self.can_stream_d
        self.consumer.write(data)

    def allDataReceived(self):
        self.finished.callback(None)

    def resumeProducing(self):
        pass

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class FakeBody(object):
    implements(IBodyProducer)
    
    msg = 'a'*50
    length = 50

    def startProducing(self, consumer):
        consumer.write(self.msg)

    def stopProducing(self):
        pass


class BodyStreamer(protocol.Protocol):
    def __init__(self, streamfunction, finished):
        self._finished = finished
        self._streamfunction = streamfunction

    def dataReceived(self, data):
        self._streamfunction(data)

    def connectionLost(self, reason):
        self._finished.callback(None)


class HTTPStreamProxyRequest(http.Request):

    def handleForwardPart(self, data):
        print('writing some data')
        self.write(data)

    def handleForwardEnd(self, data):
        print("ForwardEnded")
        if data is not None:
            self.write(data)
        self.unregisterProducer()
        self.finish()
        print("Finished")

    def handleError(self, failure):
        print("error occured %s" % failure)
        self.close()

    def cbResponse(self, response):
        print("In request Callaback")

        finished = defer.Deferred()

        #from IPython import embed; embed()
        self.responseHeaders = response.headers
        response.deliverBody(BodyStreamer(self.handleForwardPart, finished))
        finished.addCallback(self.handleForwardEnd)

        # TODO signal here that the upstream needs to close
        return finished

    def __init__(self, *args, **kwargs):
        http.Request.__init__(self, *args, **kwargs)
        print "Attaching body producer"
     
    def process(self):
   
        proxy_url = urlparse.urljoin(self.transport.protocol.proxy_url, self.uri)

        #self.transport.unregisterProducer()
        #self.transport.registerProducer(BodyProducer(), streaming=False)
        print('processing request', proxy_url)

        hdrs = self.requestHeaders
        hdrs.setRawHeaders('X-Forwarded-For', [self.getClientIP()])
        hdrs.setRawHeaders('X-I-AM', ['Goomba!!'])

        #from IPython import embed; embed()

        http_agent = Agent(reactor)
        self.proxy_d = http_agent.request(method=self.method,
                                     uri=proxy_url,
                                     headers=hdrs,
                                     bodyProducer=FakeBody())

        #self.proxy_d.addCallback(self.cbResponse)
        #self.proxy_d.addErrback(self.handleError)

        return NOT_DONE_YET

    def connectionLost(self, reason):
        print ("close conn for %s" % reason)
        try:
            if self.proxy_d:
                self.proxy_d.cancel()
        except Exception:
            pass
 
        try:
            if self.proxy_response:
                self.proxy_response._transport.stopProducing()
        except Exception:
            pass
 
        try:
            http.Request.connectionLost(self, reason)
        except Exception:
            pass


class HTTPStreamChannel(http.HTTPChannel):
    requestFactory = HTTPStreamProxyRequest

    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPChannel.__init__(self, *args, **kwargs)

        self.proxy_url = proxy_url
        self.http_agent = Agent(reactor)

    def requestReceived(self, *args, **kwargs):
        print("I got passed up")
        pass


class HTTPStreamFactory(http.HTTPFactory):

    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPFactory.__init__(self, *args, **kwargs)
        self.proxy_url = proxy_url

    def buildProtocol(self, addr):
        proto = HTTPStreamChannel(self.proxy_url)
        return proto
