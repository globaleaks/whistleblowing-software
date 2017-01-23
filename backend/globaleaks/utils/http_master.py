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
from twisted.internet.defer import inlineCallbacks

from globaleaks.models.config import PrivateFactory
from globaleaks.orm import transact
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
        # Debian will unpack the binary into /usr/bin/http_worker
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


def should_serve_https(enabled, key, cert, chain):
    # TODO(nskelsey) preform validation of key, cert, and chain as valid ASN
    # encoded objects.
    if not enabled:
        return False
    elif key == "" or cert == "" or chain == "":
        return False
    else:
        return True


class ProcessSupervisor(object):
    '''
    A Supervisor for all subprocesses that the main globaleaks process can launch
    '''

    # One child process death every 5 minutes is acceptable
    MAX_MORTALITY_RATE = 4 # 0.2

    def __init__(self, net_sockets):
        log.info("Starting process monitor")

        # TODO remove me
        self._net_sockets = net_sockets
        self.shutting_down = False

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

        # TODO move loading of DB cfg to init

    def load_file_cfg(self):
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

    def load_db_cfg(self, store):
        privFact = PrivateFactory(store)

        key = privFact.get_val('https_priv_key')
        cert = privFact.get_val('https_cert')
        chain = privFact.get_val('https_chain')
        dh_params = privFact.get_val('https_dh_params')

        self.tls_cfg['key'] = key
        self.tls_cfg['cert'] = cert
        self.tls_cfg['ssl_intermediate'] = chain
        self.tls_cfg['ssl_dh'] = dh_params

    @transact
    def maybe_launch_https_workers(self, store):
        self.db_maybe_launch_https_workers(store)

    def db_maybe_launch_https_workers(self, store):
        privFact = PrivateFactory(store)

        self.load_db_cfg(store)

        on = privFact.get_val('https_enabled')

        if should_serve_https(on, self.tls_cfg['key'],
                                  self.tls_cfg['cert'],
                                  self.tls_cfg['ssl_intermediate']):
            log.info("Decided to launch https workers")
            self.launch_https_workers()
        else:
            log.info("Not launching https workers")

    def launch_https_workers(self):
        for i in range(self.tls_process_state['target_proc_num']):
            pp = TLSProcProtocol(self, self.tls_cfg)
            log.info('Launched: %s' % (pp))
            self.tls_process_pool.append(pp)

    def handle_worker_death(self, pp, reason):
        '''
        handle_worker_death accounts the worker's death and creates a new process
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
        # TODO add logging based on condition hit

        if self.shutting_down:
            return False

        nrml_deaths = 3*self.tls_process_state['target_proc_num']

        max_deaths = nrml_deaths*50

        num_deaths = self.tls_process_state['deaths']

        return len(self.tls_process_pool) < self.tls_process_state['target_proc_num'] and \
               num_deaths < max_deaths and \
               (mort_rate < self.MAX_MORTALITY_RATE or num_deaths < nrml_deaths)

    def account_death(self):
        self.tls_process_state['deaths'] += 1
        d = self.tls_process_state['deaths']

        window = (datetime.now() - self.start_time).total_seconds()

        r = d / (window / 60.0) # deaths per minute
        log.debug('process death accountant: r=%3f, d=%2f, window=%2f' % (r, d, window))
        return r

    def shutdown(self):
        self.shutting_down = True

        log.info('Starting shutdown of %d children' % len(self.tls_process_pool))
        for pp in self.tls_process_pool:
            try:
                os.kill(pp.transport.pid, signal.SIGUSR1)
                os.kill(pp.transport.pid, signal.SIGINT)
            except OSError as e:
                log.info('Tried to signal: %d got: %s', (pp.transport.pid, e))
