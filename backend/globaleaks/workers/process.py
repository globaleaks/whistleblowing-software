# -*- encoding: utf-8 -*-
import ctypes
import json
import os
import signal
import sys

from twisted.internet import defer, reactor
from twisted.internet.protocol import ProcessProtocol

from globaleaks.utils.utility import WorkerLogger

def SigQUIT(SIG, FRM):
    WorkerLogger()('Received signal %s . . . quitting' % (SIG))
    try:
        if reactor.running:
            reactor.stop()
        else:
            sys.exit(0)
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
    # If the parent has already died, kill this process.
    if os.getppid() == 1:
        os.kill(os.getpid(), sig)


class Process(object):
    cfg = {}
    name = ''

    def __init__(self, fd=42):
        signal.signal(signal.SIGTERM, SigQUIT)
        signal.signal(signal.SIGINT, SigQUIT)
        set_proctitle(self.name)
        set_pdeathsig(signal.SIGINT)

        f = os.fdopen(fd, 'r')

        try:
            s = f.read()
        except:
            raise
        finally:
            f.close()

        self.cfg = json.loads(s)

        if self.cfg.get('debug', False):
            self.log = WorkerLogger(self.name)
        else:
            def do_nothing(m): pass
            self.log = do_nothing

    def start(self):
        reactor.run()


class CfgFDProcProtocol(ProcessProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        self.supervisor = supervisor
        self.cfg = json.dumps(cfg)
        self.cfg_fd = cfg_fd

        self.fd_map = {0:0, 1:1, 2:2}
        self.fd_map[cfg_fd] = 'w'

        self.startup_promise = defer.Deferred()

    def connectionMade(self):
        self.transport.writeToChild(self.cfg_fd, self.cfg)
        self.transport.closeChildFD(self.cfg_fd)

        # TODO Wipe the cfg dict safely
        del self.cfg

        self.startup_promise.callback(None)

    def processEnded(self, reason):
        self.supervisor.handle_worker_death(self, reason)

    def __repr__(self):
        return "<%s: %s:%s>" % (self.__class__.__name__, id(self), self.transport)


class HTTPSProcProtocol(CfgFDProcProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        CfgFDProcProtocol.__init__(self, supervisor, cfg, cfg_fd)

        for tls_socket_fd in cfg['tls_socket_fds']:
            self.fd_map[tls_socket_fd] = tls_socket_fd
