#!/usr/bin/env python
import os
import signal
from datetime import datetime


def logger():
    pid = os.getpid()
    def prefix(m):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S%z')
        print('%s [gl-tls-worker:%d] %s' % (now, pid, m))
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

# When this executable is not within the systems standard path, the globaleaks
# module must add it to sys path manually. Hence the following line.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from globaleaks.utils.process import set_pdeathsig
from globaleaks.utils.sock import listen_tls_on_sock
from globaleaks.utils.ssl import TLSServerContextFactory, ChainValidator
from globaleaks.utils.tcpproxy import ProxyServerFactory


def SigQUIT(SIG, FRM):
    log('Received %s . . . quitting' % (SIG))
    try:
        reactor.stop()
    except Exception:
        pass

signal.signal(signal.SIGTERM, SigQUIT)
signal.signal(signal.SIGINT, SigQUIT)

set_pdeathsig(signal.SIGINT)


def config_wait(file_desc):
    log("listening for cfg on %d" % file_desc)
    f = os.fdopen(file_desc, 'r')
    s = f.read()
    f.close()
    cfg = json.loads(s)
    log("read config")
    return cfg


def setup_tls_proxy(cfg):
    """
    Instantiate a TLS proxy that will handle 10,000 connections
    """
    tcp_proxy_factory = ProxyServerFactory(cfg['proxy_ip'], cfg['proxy_port'], 10000)

    cv = ChainValidator()
    cfg['https_enabled'] = False # TODO remove this for obvious reasons.
    ok = cv.validate(cfg)
    if not ok:
        raise Exception("HTTPS configuration failed validation. Not running")

    tls_factory = TLSServerContextFactory(cfg['key'],
                                    cfg['cert'],
                                    cfg['ssl_intermediate'],
                                    cfg['ssl_dh'])

    socket_fds = cfg['tls_socket_fds']

    for socket_fd in socket_fds:
        log("Opening socket: %d : %s" % (socket_fd, os.fstat(socket_fd)))

        port = listen_tls_on_sock(reactor, fd=socket_fd,
                contextFactory=tls_factory, factory=tcp_proxy_factory)

        log("TLS proxy listening on %s" % port)


if __name__ == '__main__':
    try:
        cfg = config_wait(42)
        setup_tls_proxy(cfg)
    except Exception as e:
        log("setup failed with %s" % e)
        raise e

    reactor.run()
