import json
import os

from twisted.internet.protocol import ProcessProtocol


class ProcessProtocol(ProcessProtocol):
    def __init__(self, supervisor, cfg, cfg_fd=42):
        self.supervisor = supervisor
        self.cfg = json.dumps(cfg)
        self.cfg_fd = cfg_fd

        self.fd_map = {0:0, 1:1, 2:2}
        self.fd_map[cfg_fd] = 'w'

    def connectionMade(self):
        self.transport.writeToChild(self.cfg_fd, self.cfg)
        self.transport.closeChildFD(self.cfg_fd)


        # TODO analyze how it could be possible to wipe the config
        #      that in most of the situations contains sensible information
        #      like HTTP Certificaty key
        del self.cfg

    def processEnded(self, reason):
        self.supervisor.handle_worker_death(self, reason)

    def __repr__(self):
        return "<%s: %s:%s>" % (self.__class__.__name__, id(self), self.transport)
