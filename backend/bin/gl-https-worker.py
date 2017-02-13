#!/usr/bin/env python
import os
import signal
from datetime import datetime


def logger():
    pid = os.getpid()
    def prefix(m):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S%z')
        print('%s [gl-https-worker:%d] %s' % (now, pid, m))
    return prefix


# WARN signalling in this way is a race condition.
def SigRespond(SIG, FRM):
    log("Received sig: %s from %s" % (FRM, SIG))


log = logger()
log('started')

signal.signal(signal.SIGUSR1, SigRespond)


import json
import socket
import sys

from twisted.internet import reactor, ssl, protocol, defer
from twisted.protocols import tls
from twisted.web.http import HTTPFactory

# When this executable is not within the systems standard path, the globaleaks
# module must add it to sys path manually. Hence the following line.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from globaleaks.utils.process import set_pdeathsig
from globaleaks.utils.sock import open_socket_listen, listen_tcp_on_sock
from globaleaks.utils.tls import TLSServerContextFactory, ChainValidator
from globaleaks.utils.tcpproxy import ProxyServerFactory
from globaleaks.utils.streamer import HTTPStreamFactory


def SigQUIT(SIG, FRM):
    log('Received %s . . . quitting' % (SIG))
    try:
        reactor.stop()
    except Exception:
        pass

signal.signal(signal.SIGTERM, SigQUIT)
signal.signal(signal.SIGINT, SigQUIT)

set_pdeathsig(signal.SIGINT)


def setup_https_proxy():
    iface, port = '127.0.0.1', 7000
    proxy_url = 'http://127.0.0.1:8082'

    cfg = {
        # 'ssl_key':
        #
    }

    http_proxy_factory = HTTPStreamFactory(proxy_url)
    sock = open_socket_listen(iface, port)
    listen_tcp_on_sock(reactor, sock.fileno(), http_proxy_factory)

    log('Listening on %s:%d' % (iface, port))
    log('Forwarding requests to: %s' % proxy_url)

if __name__ == '__main__':
    setup_https_proxy()
    reactor.run()
