import urlparse

from zope.interface import implements

from twisted.web import http, client, _newclient
from twisted.web.client import Agent
from twisted.internet import reactor, protocol, defer, address
from twisted.web.iweb import IBodyProducer
from twisted.web.server import NOT_DONE_YET


class BodyStreamer(protocol.Protocol):
    def __init__(self, streamfunction, finished):
        self._finished = finished
        self._streamfunction = streamfunction

    def dataReceived(self, data):
        self._streamfunction(data)

    def connectionLost(self, reason):
        self._finished.callback('')


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
    
    CHUNK_SIZE = 1024
    length = _newclient.UNKNOWN_LENGTH

    deferred = None
    inp_buf = None

    def __init__(self, io_buf):
        self.inp_buf = io_buf
        self.deferred = defer.Deferred()


    def startProducing(self, consumer):
        return self.resumeProducing(consumer)

    def resumeProducing(self, consumer):
        chunk = self.inp_buf.read(self.CHUNK_SIZE)
        print ("writing chunk", chunk)
        consumer.write(chunk)
        self.deferred.callback(None)
        print("Finished")
        return self.deferred

    def stopProducing(self):
        self.deferred = None
        self.inp_buf.close()

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
        finished.addErrback(self.handleError)

        # TODO signal here that the upstream needs to close
        return finished

    def __init__(self, *args, **kwargs):
        http.Request.__init__(self, *args, **kwargs)
     
    def process(self):
   
        proxy_url = urlparse.urljoin(self.transport.protocol.proxy_url, self.uri)

        #self.transport.unregisterProducer()
        #self.transport.registerProducer(BodyProducer(), streaming=False)
        print('processing request', proxy_url)

        hdrs = self.requestHeaders
        hdrs.setRawHeaders('X-Forwarded-For', [self.getClientIP()])
        hdrs.setRawHeaders('X-I-AM', ['Goomba!!'])

        #from IPython import embed; embed()
        #self.content.seek(0,0)
        prod = FakeBody(self.content)

        http_agent = Agent(reactor)
        self.proxy_d = http_agent.request(method=self.method,
                                     uri=proxy_url,
                                     headers=hdrs,
                                     bodyProducer=prod)

        self.proxy_d.addCallback(self.cbResponse)
        self.proxy_d.addErrback(self.handleError)

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
