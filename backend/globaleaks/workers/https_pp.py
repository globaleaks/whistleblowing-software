import json
import os
from sys import executable

from twisted.internet import reactor, protocol

from globaleaks.utils.utility import log


class HTTPSProcProtocol(protocol.ProcessProtocol):
    def __init__(self, supervisor, bin_path, cfg, cfg_fd=42):
        self.supervisor = supervisor
        self.cfg = json.dumps(cfg)
        self.cfg_fd = cfg_fd

        fd_map = {0:0, 1:1, 2:2}
        fd_map[cfg_fd] = 'w'

        tls_socket_fds = cfg['tls_socket_fds']

        for tls_socket_fd in tls_socket_fds:
            fd_map[tls_socket_fd] = tls_socket_fd
            log.debug('State of fd: <%d> %s' % (tls_socket_fd, os.fstat(tls_socket_fd)))

        log.debug('subproc fd_map:%s' % (fd_map))

        reactor.spawnProcess(self, executable, [executable, bin_path], childFDs=fd_map, env=os.environ)

    def connectionMade(self):
        log.info("Parent writing to: %d" % self.cfg_fd)
        self.transport.writeToChild(self.cfg_fd, self.cfg)
        self.transport.closeChildFD(self.cfg_fd)
        # TODO self.cfg has a copy of TLS priv_key
        del self.cfg

    def processEnded(self, reason):
        self.supervisor.handle_worker_death(self, reason)

    def __repr__(self):
        return "<HTTPSProcProtocol: %s:%s>" % (id(self), self.transport)
