# -*- encoding: utf-8 -*-
import json
import os
import signal
import sys
import traceback

from twisted.internet import defer, reactor
from twisted.internet.protocol import ProcessProtocol

from globaleaks.utils.process import set_proc_title, set_pdeathsig, disable_swap
from globaleaks.utils.utility import log

class Process(object):
    cfg = {}
    name = ''

    def __init__(self, fd=42):
        self.pid = os.getpid()

        set_proc_title(self.name)
        set_pdeathsig(signal.SIGINT)

        def _shutdown(SIG, FRM):
            self.shutdown()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)
        signal.signal(signal.SIGUSR1, _shutdown)

        def excepthook(*exc_info):
            self.log("".join(traceback.format_exception(*exc_info)))

        sys.excepthook = excepthook

        with os.fdopen(fd, 'r') as f:
            self.cfg = json.loads(f.read())

    def shutdown(self):
        if reactor.running:
            reactor.stop()
        else:
            sys.exit(0)

    def start(self):
        reactor.run()

    def log(self, m):
        if self.cfg.get('debug', False):
            with os.fdopen(0, 'w', 1) as f:
                f.write('[%s:%d] %s\n' % (self.name, self.pid, m))


class CfgFDProcProtocol(ProcessProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        self.supervisor = supervisor
        self.cfg = json.dumps(cfg)
        self.cfg_fd = cfg_fd

        self.fd_map = {0:'r', cfg_fd:'w'}

        self.startup_promise = defer.Deferred()

    def connectionMade(self):
        self.transport.writeToChild(self.cfg_fd, self.cfg)
        self.transport.closeChildFD(self.cfg_fd)

        self.startup_promise.callback(None)

    def childDataReceived(self, childFD, data):
        for line in data.split('\n'):
            if line != '':
                log.debug(line)

    def processEnded(self, reason):
        self.supervisor.handle_worker_death(self, reason)

    def __repr__(self):
        return "<%s: %s:%s>" % (self.__class__.__name__, id(self), self.transport)


class HTTPSProcProtocol(CfgFDProcProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        CfgFDProcProtocol.__init__(self, supervisor, cfg, cfg_fd)

        for tls_socket_fd in cfg['tls_socket_fds']:
            self.fd_map[tls_socket_fd] = tls_socket_fd
