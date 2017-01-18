#!/usr/bin/env python
print('[subproc] reached python')

import json
import os
import signal
import socket
import sys

# WARN signalling in this way is a race condition.
def SigRespond(SIG, FRM):
    print('responding')
    p = os.getpid()
    print("[subproc]:%d received note from: %s : %s" % (p, FRM, SIG))

signal.signal(signal.SIGUSR1, SigRespond)

from twisted.internet import reactor, ssl, protocol, defer
from twisted.protocols import tls
from twisted.web.proxy import ReverseProxyResource
from twisted.web.server import Site

# When this executable is not within the systems standard path, the globaleaks
# module must add it to sys path manually. Hence the following line.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from globaleaks.utils.process import set_pdeathsig
from globaleaks.utils.socket import listen_tls_on_sock
from globaleaks.utils.ssl import TLSContextFactory


def SigQUIT(SIG, FRM):
    print('Quitting')
    try:
        reactor.stop()
    except Exception:
        pass

signal.signal(signal.SIGTERM, SigQUIT)
signal.signal(signal.SIGINT, SigQUIT)

set_pdeathsig(signal.SIGINT)

def config_wait(file_desc):
    print("[subproc] subprocess listening for cfg from: %d" % file_desc)
    f = os.fdopen(file_desc, 'r')
    s = f.read()
    f.close()
    config = json.loads(s)
    print("[subproc] read config!")
    return config

def setup_tls_proxy(config):
    resource = ReverseProxyResource('127.0.0.1', 8082, '')
    http_factory = Site(resource)

    for fd in config['fds']:
        tls_factory = TLSContextFactory(config['ssl_key'],
                                        config['ssl_cert'],
                                        config['ssl_intermediate'],
                                        config['ssl_dh'],
                                        config['ssl_cipher_list'])

        print("[subproc] TLS proxy listening on %d" % fd)
        port = listen_tls_existing_sock(reactor, fd=fd, factory=http_factory,
                                        contextFactory=tls_factory)

if __name__ == '__main__':
    try:
        cfg = config_wait(42)

        setup_tls_proxy(cfg)
    except Exception as e:
        print("[subproc] setup failed for %s" % e)
        raise e

    reactor.run()
