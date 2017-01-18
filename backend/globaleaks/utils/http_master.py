import json
import multiprocessing
import os
import signal
import socket
import sys
import signal

from sys import executable

from twisted.internet import reactor, ssl, task, protocol, defer
from twisted.protocols import tls
from twisted.python.compat import urllib_parse, urlquote
from twisted.web import proxy, resource, server

from OpenSSL import SSL
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from OpenSSL._util import lib as _lib, ffi as _ffi

from globaleaks.utils import as socket_util
from globaleaks.utils.utility import log


def instantiate_pool(config):
    process_pool = []
        return process_pool


class ConfigureProtocol(protocol.ProcessProtocol):

  def __init__(self, supervisor, cfg, cfg_fd):
    self.cfg = json.dumps(cfg)
    self.cfg_fd = cfg_fd

  def connectionMade(self):
    print("Parent writing to: %d" % self.cfg_fd)
    self.transport.writeToChild(self.cfg_fd, self.cfg)
    self.transport.closeChildFD(self.cfg_fd)
    print('resolving connect')

  def processExited(self, reason):
    log.info("Subprocess[%d] exited with[%s] for: %s" % (self.transport.pid,
                                             self.transport.status, reason))

    self.supervisor.handle_worker_death(self, reason)


class ProcessSupervisor(object):
    tls_process_pool = None
    tls_cfg = None

    def __init__(self, net_sockets):
        log.info("Starting process monitor")

        self.tls_process_pool = []

        self.tls_cfg = {
          'ip': '127.0.0.1',
          'port': 443,
          'tls_sock_fd': net_sockets['https'],
          'ssl_cipher_list': 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-AES128-SHA',
        }

        with open('/home/nskelsey/scratch/key.pem', 'r') as f:
            self.tls_cfg['key'] = f.read()

        with open('/home/nskelsey/scratch/cert.pem', 'r') as f:
            self.tls_cfg['cert'] = f.read()

        with open('/home/nskelsey/scratch/fullchain1.pem', 'r') as f:
            self.tls_cfg['chain'] = f.read()

        with open('/home/nskelsey/scratch/dh.pem', 'r') as f:
            self.tls_cfg['dh_param'] = f.read()

        self.launch_https_workers()

    def launch_all_https_workers(self):
        config = self.tls_cfg

        for i in range(multiprocessing.cpu_count()):
                pp = self.launch_https_worker(self.tls_cfg, self.)
                self.tls_process_pool.append(pp)

    @staticmethod
    def launch_https_worker(config, tls_sock_fd, cfg_fd=42):
        pp = ConfigureProtocol(config, tls_sock_fd, cfg_fd)

        path = '/home/nskelsey/projects/globaleaks/backend/bin/http_worker.py'
        fd_map = {0:0, 1:1, 2:2}
        fd_map[cfg_fd] = 'w'

        tls_sock_fd = config['tls_sock_fd']
        fd_map[tls_sock_fd] = tls_sock_fd

        reactor.spawnProcess(pp, executable, [executable, path], childFDs=fd_map, env=os.environ)
        print('Launched: %s; %s; with fd_map: %s' % (pp, pp.transport, fd_map))
        return pp

    def handle_worker_death(self, pp, reason):
        # TODO create a new process in its place if the reason for death is
        # reasonable and we haven't restarted the child an unreasonable number
        # of times.
        pass

    def shutdown(self):
        for pp in self.tls_process_pool:
            try:
                os.kill(pp.transport.pid, signal.SIGUSR0)
            except OSError as e:
                log.info('Tried to signal: %d got: %s', (pp.transport.pid, e))


