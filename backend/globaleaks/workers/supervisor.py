# -*- coding: utf-8 -*-
import logging
import multiprocessing
import os
import signal
from sys import executable

from twisted.internet import defer, reactor

from globaleaks.handlers.admin.https import load_tls_dict_list
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact
from globaleaks.utils import tls
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601
from globaleaks.utils.log import log
from globaleaks.workers.process import HTTPSProcProtocol


class ProcessSupervisor(object):
    """
    A supervisor for all subprocesses that the main globaleaks process can launch
    """
    def __init__(self, net_sockets, proxy_ip, proxy_port):
        log.info("Starting process monitor")

        self.shutting_down = False

        self.start_time = datetime_now()
        self.tls_process_pool = []
        self.cpu_count = multiprocessing.cpu_count()

        self.worker_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'worker_https.py')

        self.tls_cfg = {
          'proxy_ip': proxy_ip,
          'proxy_port': proxy_port,
          'debug': log.loglevel <= logging.DEBUG,
          'site_cfgs': [],
        }

        if not net_sockets:
            log.err("No ports to bind to! Spawning processes will not work!")

        self.tls_cfg['tls_socket_fds'] = [ns.fileno() for ns in net_sockets]

    def db_maybe_launch_https_workers(self, session):
        config = ConfigFactory(session, 1)

        # If root_tenant is disabled do not start https
        on = config.get_val(u'https_enabled')
        if not on:
            log.info("Not launching workers")
            return defer.succeed(None)

        site_cfgs = load_tls_dict_list(session)

        valid_cfgs, err = [], None
        # Determine which site_cfgs are valid and only pass those to the child.
        for db_cfg in site_cfgs:
            chnv = tls.ChainValidator()
            ok, err = chnv.validate(db_cfg, must_be_disabled=False, check_expiration=False)
            if ok and err is None:
                valid_cfgs.append(db_cfg)

        self.tls_cfg['site_cfgs'] = valid_cfgs

        if not valid_cfgs:
            log.info("Not launching https workers due to %s", err)
            return defer.fail(err)

        log.info("Decided to launch https workers")

        return self.launch_https_workers()

    @transact
    def maybe_launch_https_workers(self, session):
        self.db_maybe_launch_https_workers(session)

    def launch_worker(self):
        pp = HTTPSProcProtocol(self, self.tls_cfg)
        reactor.spawnProcess(pp, executable, [executable, self.worker_path], childFDs=pp.fd_map, env=os.environ)
        self.tls_process_pool.append(pp)

        log.info('Launched: %s', pp)

        return pp.startup_promise

    def launch_https_workers(self):
        return defer.DeferredList([self.launch_worker() for _ in range(self.cpu_count)])

    def should_spawn_child(self):
        return not self.shutting_down and len(self.tls_process_pool) < self.cpu_count

    def is_running(self):
        return len(self.tls_process_pool) > 0

    def handle_worker_death(self, pp, reason):
        log.debug("Subprocess: %s exited with: %s", pp, reason)

        if pp in self.tls_process_pool: self.tls_process_pool.remove(pp)

        if self.should_spawn_child():
            self.launch_worker()

    def get_status(self):
        if self.is_running():
            msg = "Everything is running normally."
        elif not self.should_spawn_child():
            msg = "The supervisor will not create new workers"
        else:
            msg = "Nothing is being served"

        return {
            'timestamp': datetime_to_ISO8601(datetime_now()),
            'msg': msg
        }

    def reload(self):
        log.debug('Reloading HTTPS configuration')

        while self.tls_process_pool:
            try:
                pp = self.tls_process_pool.pop(0)
                pp.transport.signalProcess(signal.SIGUSR2)
            except OSError as e:
                log.debug('Tried to signal: %d got: %s', pp.transport.pid, e)

        self.launch_https_workers()

    def shutdown(self):
        log.debug('Starting HTTPS workes shutdown')

        self.shutting_down = True

        while self.tls_process_pool:
            try:
                pp = self.tls_process_pool.pop(0)
                pp.transport.signalProcess(signal.SIGUSR1)
            except OSError as e:
                log.debug('Tried to signal: %d got: %s', pp.transport.pid, e)
