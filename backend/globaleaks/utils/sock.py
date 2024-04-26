# -*- coding: utf-8 -*-
import fcntl
import socket

from twisted.internet import abstract
from twisted.protocols import tls


def isIPAddress(hostname):
    return abstract.isIPAddress(hostname) or abstract.isIPv6Address(hostname)


def listen_tcp_on_sock(reactor, fd, factory):
    return reactor.adoptStreamPort(fd, socket.AF_INET6, factory)


def listen_tls_on_sock(reactor, fd, contextFactory, factory):
    tlsFactory = tls.TLSMemoryBIOFactory(contextFactory, False, factory)
    port = listen_tcp_on_sock(reactor, fd, tlsFactory)
    port._type = 'TLS'
    return port


def open_socket_listen(ip, port):
    if abstract.isIPv6Address(ip):
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setblocking(False)

    flags = fcntl.fcntl(s, fcntl.F_GETFD)
    fcntl.fcntl(s, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)

    s.bind((ip, port))
    s.listen(4096)

    return s


def reserve_tcp_socket(ip, port):
    try:
        sock = open_socket_listen(ip, port)
        return [sock, None]
    except Exception as err:
        return [None, err]
