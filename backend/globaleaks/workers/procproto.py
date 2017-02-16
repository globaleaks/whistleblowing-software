import json
import os

from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet.protocol import ProcessProtocol


class ProcessProtocol(ProcessProtocol):
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
