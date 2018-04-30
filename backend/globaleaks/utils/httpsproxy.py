# -*- coding: utf-8 -*-
import io
import sys

from six.moves import urllib

from twisted.internet import reactor, protocol, defer
from twisted.internet.protocol import connectionDone
from twisted.web import http
from twisted.web.client import Agent
from twisted.web.iweb import IBodyProducer
from twisted.web.server import NOT_DONE_YET
from zope.interface import implementer


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


@implementer(IBodyProducer)
class BodyProducer(object):

    BUF_MAX_SIZE = 64 * 1024 # TODO Use the hardcoded value for buf max size
    length = 0
    bytes_written = 0

    deferred = None
    inp_buf = None
    rf_buf_fn = None
    consumer = None

    def __init__(self, inp_buf, rf_buf_fn, length):
        self.inp_buf = inp_buf
        self.rf_buf_fn = rf_buf_fn
        self.length = length
        self.deferred = defer.Deferred()

    def startProducing(self, consumer):
        self.consumer = consumer
        return self.resumeProducing()

    def resumeProducing(self):
        chunk = self.inp_buf.read()
        n = len(chunk)
        if n != 0:
            self.consumer.write(chunk)
            self.bytes_written += n
            if self.bytes_written > self.BUF_MAX_SIZE:
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
        if hasattr(self.content, 'close'):
            self.content.close()
            self.content = io.BytesIO()
            self.reset_buffer()

    def process(self):
        joined_url = urllib.parse.urljoin(self.channel.proxy_url.encode('utf-8'), self.uri)
        hdrs = self.requestHeaders
        hdrs.setRawHeaders(b'GL-Forwarded-For', [self.getClientIP()])

        prod = None
        content_length = self.getHeader(b'Content-Length')
        if content_length is not None:
            hdrs.removeHeader(b'Content-Length')
            prod = BodyProducer(self.content, self.reset_buffer, int(content_length))
            self.registerProducer(prod, streaming=True)

        proxy_d = self.channel.http_agent.request(method=self.method,
                                                  uri=joined_url,
                                                  headers=hdrs,
                                                  bodyProducer=prod)
        if prod is not None:
            proxy_d.addBoth(self.proxyUnregister)

        proxy_d.addCallback(self.proxySuccess)
        proxy_d.addErrback(self.proxyError)

        return NOT_DONE_YET

    def proxySuccess(self, response):
        self.responseHeaders = response.headers

        self.responseHeaders.setRawHeaders(b'Strict-Transport-Security', [b'max-age=31536000'])

        self.setResponseCode(response.code)

        d_forward = defer.Deferred()

        response.deliverBody(BodyStreamer(self.write, d_forward))

        d_forward.addBoth(self.forwardClose)

    def proxyError(self, fail):
        # Always apply the HSTS header. Compliant browsers using plain HTTP will ignore it.
        self.responseHeaders.setRawHeaders(b'Strict-Transport-Security', [b'max-age=31536000'])
        self.setResponseCode(502)
        self.forwardClose()

    def proxyUnregister(self, o):
        self.unregisterProducer()
        return o

    def forwardClose(self, *args):
        self.content.close()
        self.finish()


class HTTPStreamChannel(http.HTTPChannel):
    requestFactory = HTTPStreamProxyRequest

    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPChannel.__init__(self, *args, **kwargs)

        self.proxy_url = proxy_url
        self.http_agent = Agent(reactor, connectTimeout=30)


class HTTPStreamFactory(http.HTTPFactory):
    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPFactory.__init__(self, *args, **kwargs)
        self.proxy_url = proxy_url
        self.active_connections = 0

    def buildProtocol(self, addr):
        proto = HTTPStreamChannel(self.proxy_url)
        _connectionMade = proto.connectionMade
        _connectionLost = proto.connectionLost

        def connectionMade(*args):
            self.active_connections += 1
            return _connectionMade(*args)

        def connectionLost(*args):
            self.active_connections -= 1
            return _connectionLost(*args)

        proto.connectionMade = connectionMade
        proto.connectionLost = connectionLost

        return proto
