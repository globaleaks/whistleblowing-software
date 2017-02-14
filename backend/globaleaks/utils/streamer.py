import urlparse
import io

from zope.interface import implements

from twisted.web import http, client, _newclient
from twisted.web.client import Agent
from twisted.internet import reactor, protocol, defer, address
from twisted.internet.protocol import connectionDone
from twisted.web.iweb import IBodyProducer
from twisted.web.server import NOT_DONE_YET


class BodyStreamer(protocol.Protocol):
    def __init__(self, streamfunction, finished):
        self._finished = finished
        self._streamfunction = streamfunction

    def dataReceived(self, data):
        self._streamfunction(data)

    def connectionLost(self, reason=connectionDone):
        self._streamfunction = None
        self._finished.callback(None)
        self._finished = None


class BodyProducer(object):
    implements(IBodyProducer)

    BUF_MAX_SIZE = 2*1023*1024 # TODO Use the hardcoded value for buf max size
    length = 0
    bytes_written = 0

    deferred = None
    inp_buf = None
    rf_buf_fn = None
    consumer = None

    def __init__(self, inp_buf, rf_buf_fn, length):
        print("inp_buf type: %s" % type(inp_buf))
        self.inp_buf = inp_buf
        self.rf_buf_fn = rf_buf_fn
        self.length = length
        self.deferred = defer.Deferred()

    def startProducing(self, consumer):
        print("startProducing: %s" % consumer)
        self.consumer = consumer
        return self.resumeProducing()

    def resumeProducing(self):
        chunk = self.inp_buf.read()
        n = len(chunk)
        print("resumeProducing() n = %d" % n)
        if n != 0:
            self.consumer.write(chunk)
            self.bytes_written += n
            if self.bytes_written > self.BUF_MAX_SIZE:
                print("Install buffer")
                self.inp_buf = self.rf_buf_fn()
                self.bytes_written = 0
        else:
            self.deferred.callback(None)

        return self.deferred

    def stopProducing(self):
        self.deferred = None
        self.inp_buf.close()
        self.rf_buf_fn = None
        self.consumer = None

    def pauseProducing(self):
        pass


class HTTPStreamProxyRequest(http.Request):
    def __init__(self, *args, **kwargs):
        http.Request.__init__(self, *args, **kwargs)

    def reset_buffer(self):
        self.content.seek(0, 0)
        self.content.truncate(0)
        return self.content

    def gotLength(self, length):
        http.Request.gotLength(self, length)
        if isinstance(self.content, file):
            print('Found tmpfile, replacing')
            #TODO must close tmpfile
            self.content = io.BytesIO()
            self.reset_buffer()

    def process(self):
        proxy_url = urlparse.urljoin(self.transport.protocol.proxy_url, self.uri)
        print('proxying: %s' % proxy_url)

        hdrs = self.requestHeaders
        hdrs.setRawHeaders('X-Forwarded-For', [self.getClientIP()])

        prod = None
        content_length = self.getHeader('Content-Length')
        if content_length is not None:
            hdrs.removeHeader('Content-Length')
            print('Found: %s' % content_length)
            prod = BodyProducer(self.content, self.reset_buffer, int(content_length))
            self.registerProducer(prod, streaming=True)

        http_agent = Agent(reactor, connectTimeout=2)
        proxy_d = http_agent.request(method=self.method,
                                     uri=proxy_url,
                                     headers=hdrs,
                                     bodyProducer=prod)

        reactor.callLater(15, proxy_d.cancel)
        proxy_d.addCallback(self.proxySuccess)
        proxy_d.addErrback(self.proxyError)

        return NOT_DONE_YET

    def proxySuccess(self, response):
        print("proxySuccess: %s" % response)
        self.unregisterProducer()
        self.responseHeaders = response.headers

        d_forward = defer.Deferred()
        response.deliverBody(BodyStreamer(self.write, d_forward))
        d_forward.addBoth(self.forwardClose)

    def proxyError(self, fail):
        print("proxyErr: %s" % fail)
        # TODO respond with 500
        self.unregisterProducer()
        self.forwardClose()

    def forwardClose(self, *args):
        print("forwardClose()")
        self.unregisterProducer()
        self.content.close()
        self.finish()
        print("handled close")


class HTTPStreamChannel(http.HTTPChannel):
    requestFactory = HTTPStreamProxyRequest

    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPChannel.__init__(self, *args, **kwargs)

        self.proxy_url = proxy_url
        self.http_agent = Agent(reactor)


class HTTPStreamFactory(http.HTTPFactory):

    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPFactory.__init__(self, *args, **kwargs)
        self.proxy_url = proxy_url

    def buildProtocol(self, addr):
        proto = HTTPStreamChannel(self.proxy_url)
        return proto
