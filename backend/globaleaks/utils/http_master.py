import json
import multiprocessing
import os
import signal
import socket
import sys
import signal

from datetime import datetime
from sys import executable

from twisted.internet import reactor, task, protocol, defer

from globaleaks.utils import sock as socket_util
from globaleaks.utils.utility import log


class TLSProcProtocol(protocol.ProcessProtocol):

  def __init__(self, supervisor, cfg, cfg_fd=42):
    self.supervisor = supervisor
    self.cfg = json.dumps(cfg)
    self.cfg_fd = cfg_fd

    fd_map = {0:0, 1:1, 2:2}
    fd_map[cfg_fd] = 'w'

    tls_socket_fd = cfg['tls_socket_fd']
    fd_map[tls_socket_fd] = tls_socket_fd
    
    log.debug('subproc fd_map:%s, tls_socket_fd:%d, os_fstat=%s' % (fd_map, 
              tls_socket_fd, os.fstat(tls_socket_fd)))

    # TODO remove abs path.
    path = '/home/nskelsey/projects/globaleaks/backend/bin/http_worker.py'
    reactor.spawnProcess(self, executable, [executable, path], childFDs=fd_map, env=os.environ)

  def connectionMade(self):
    log.info("Parent writing to: %d" % self.cfg_fd)
    self.transport.writeToChild(self.cfg_fd, self.cfg)
    self.transport.closeChildFD(self.cfg_fd)
    # TODO self.cfg has a copy of TLS cert key
    del self.cfg

  def processEnded(self, reason):
    self.supervisor.handle_worker_death(self, reason)

  def __repr__(self):
      return "<TLSProcProtocol: %s:%s>" % (id(self), self.transport)


class ProcessSupervisor(object):

    # One child process death every 5 minutes is acceptable
    MAX_MORTALITY_RATE = 25 # 0.2

    def __init__(self, net_sockets):
        log.info("Starting process monitor")

        # TODO remove me
        self._net_sockets = net_sockets

        self.start_time = datetime.now()
        self.tls_process_pool = []
        self.tls_process_state = {
            'deaths': 0,
            'last_death': datetime.now(),
            'target_proc_num': multiprocessing.cpu_count(),
        }

        self.tls_cfg = {
          'proxy_ip': '127.0.0.1',
          'proxy_port': 8082,
          'tls_socket_fd': net_sockets['https'].fileno(),
          'ssl_cipher_list': 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-AES128-SHA',
        }

        # TODO use values passed from storm
        root_path = '/home/nskelsey/scratch/'
        with open(root_path+'key.pem', 'r') as f:
            self.tls_cfg['key'] = f.read()

        with open(root_path+'cert.pem', 'r') as f:
            self.tls_cfg['cert'] = f.read()

        with open(root_path+'fullchain1.pem', 'r') as f:
            self.tls_cfg['ssl_intermediate'] = f.read()

        with open(root_path+'dh.pem', 'r') as f:
            self.tls_cfg['ssl_dh'] = f.read()

        # TODO launch later
        self.launch_https_workers()

    def launch_https_workers(self):
        for i in range(self.tls_process_state['target_proc_num']):
            pp = TLSProcProtocol(self, self.tls_cfg)
            log.info('Launched: %s' % (pp))
            self.tls_process_pool.append(pp)

    def handle_worker_death(self, pp, reason):
        '''
        handle_worker_death accounts the workers death and creates a new process
        in its place if the reason for death is reasonable and we haven't
        restarted the child an unreasonable number of times.
        '''
        log.info("Subprocess: %s exited with: %s" % (pp, reason))
        mortatility_rate = self.account_death()
        self.tls_process_pool.pop(self.tls_process_pool.index(pp))
        del pp

        #self.tls_cfg['tls_socket_fd'] = self._net_sockets['https'].fileno()
        if (self.should_spawn_child(mortatility_rate)):
            pp = TLSProcProtocol(self, self.tls_cfg)
            log.info('Relaunched: %s' % (pp))
            self.tls_process_pool.append(pp)
        else:
            log.err("Not relaunching child process")

    def should_spawn_child(self, mort_rate):
        nrml_deaths = 3*self.tls_process_state['target_proc_num']

        return len(self.tls_process_pool) < self.tls_process_state['target_proc_num'] and \
               (mort_rate < self.MAX_MORTALITY_RATE or self.tls_process_state['deaths'] < nrml_deaths)

    def account_death(self):
        self.tls_process_state['deaths'] += 1
        d = self.tls_process_state['deaths']

        window = (datetime.now() - self.start_time).total_seconds()

        r = d / (window / 60.0) # deaths per minute
        log.debug('process death accountant: r=%f, d=%f, window=%f' % (r, d, window))
        return r

    def shutdown(self):
        # TODO function is unused
        for pp in self.tls_process_pool:
            try:
                os.kill(pp.transport.pid, signal.SIGUSR0)
            except OSError as e:
                log.info('Tried to signal: %d got: %s', (pp.transport.pid, e))
