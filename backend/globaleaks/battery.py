# -*- coding: UTF-8
#   battery
#
# Implement a battery of HTTP Servers distributing the GZIP compression on multiple cores
import ast
import ctypes
import multiprocessing
import os
import signal

from sys import executable

from socket import AF_INET

from twisted.internet import reactor, protocol
from twisted.web.server import Site

from twisted.web.server import Site, GzipEncoderFactory
from twisted.web.resource import EncodingResourceWrapper
from twisted.web import proxy
from twisted.internet import reactor

def SigQUIT(SIG, FRM):
    try:
        reactor.stop()
    except Exception:
        pass


def set_proctitle(title):
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    buff = ctypes.create_string_buffer(len(title) + 1)
    buff.value = title
    libc.prctl(15, ctypes.byref(buff), 0, 0, 0)


def set_pdeathsig(sig):
    PR_SET_PDEATHSIG = 1
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    libc.prctl.argtypes = (ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                           ctypes.c_ulong, ctypes.c_ulong)
    libc.prctl(PR_SET_PDEATHSIG, sig, 0, 0, 0)


class GLPP(protocol.ProcessProtocol):
    def processExited(self, reason):
        reactor.stop()


class ReverseProxyGzipResource(proxy.ReverseProxyResource):
    def getChild(self, path, request):
        child = ReverseProxyGzipResource(
            self.host, self.port, self.path + b'/' + proxy.urlquote(path, safe=b"").encode('utf-8'),
            self.reactor)

        return EncodingResourceWrapper(child, [GzipEncoderFactory()])


def main(ips, port, fds):
    resource = ReverseProxyGzipResource('127.0.0.1', 8083, '')
    factory = Site(resource)

    if len(fds) == 0:
        for ip in ips:
            fds.append(reactor.listenTCP(port, factory, 50, ip).fileno())

        childFDs = {}
        for fd in fds:
            childFDs[fd] = fd

        env = os.environ.copy()
        env['listening_fds'] = str(fds)

        for i in range(multiprocessing.cpu_count() - 1):
            reactor.spawnProcess(GLPP(),
                                 executable,
                                 [executable, __file__],
                                 childFDs=childFDs,
                                 env=env)
    else:
        for fd in fds:
            reactor.adoptStreamPort(fd, AF_INET, factory)

    reactor.run()


processes = multiprocessing.cpu_count() - 1

signal.signal(signal.SIGINT, SigQUIT)
set_pdeathsig(signal.SIGINT)
set_proctitle('globaleaks-http')

ips = ast.literal_eval(os.environ.get('listening_ips', '[]'))
fds = ast.literal_eval(os.environ.get('listening_fds', '[]'))
port = int(os.environ.get('listening_port', 8082))

if len(ips):
    main(ips, port, fds)
