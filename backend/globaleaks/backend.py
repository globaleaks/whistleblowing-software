# -*- coding: utf-8
#   backend
#   *******
import os
import sys
import traceback

from datetime import datetime

from twisted.application import service
from twisted.internet import reactor, defer
from twisted.python import log as txlog, logfile as txlogfile
from twisted.web.http import _escape
from twisted.web.server import Site

from globaleaks.state import State
from globaleaks.db import init_db, update_db, \
    sync_refresh_memory_variables, sync_clean_untracked_files
from globaleaks.rest.api import APIResourceWrapper
from globaleaks.settings import Settings
from globaleaks.utils.process import disable_swap
from globaleaks.utils.sock import listen_tcp_on_sock, reserve_port_for_ip
from globaleaks.utils.utility import log, timedelta_to_milliseconds, GLLogObserver, deferred_sleep
from globaleaks.workers.supervisor import ProcessSupervisor

# this import seems unused but it is required in order to load the mocks
import globaleaks.mocks.twisted_mocks # pylint: disable=W0611


def fail_startup(excep):
    log.err("ERROR: Cannot start GlobaLeaks. Please manually examine the exception.")
    log.err("EXCEPTION: %s",  excep)
    log.debug('TRACE: %s', traceback.format_exc(excep))
    if reactor.running:
        reactor.stop()


def timedLogFormatter(timestamp, request):
    duration = -1
    if hasattr(request, 'start_time'):
        duration = timedelta_to_milliseconds(datetime.now() - request.start_time)

    return (u'%(code)s %(method)s %(uri)s %(length)dB %(duration)dms' % dict(
              duration=duration,
              method=_escape(request.method),
              uri=_escape(request.uri),
              proto=_escape(request.clientproto),
              code=request.code,
              length=request.sentLength))


class Service(service.Service):
    def __init__(self):
        self.state = State

        self.arw = APIResourceWrapper()
        self.api_factory = Site(self.arw, logFormatter=timedLogFormatter)

    def startService(self):
        mask = 0
        if Settings.devel_mode:
            mask = 8000

        # Allocate local ports
        for port in Settings.bind_local_ports:
            http_sock, fail = reserve_port_for_ip('127.0.0.1', port)
            if fail is not None:
                log.err("Could not reserve socket for %s (error: %s)", fail[0], fail[1])
            else:
                self.state.http_socks += [http_sock]

        # Allocate remote ports
        for port in Settings.bind_remote_ports:
            sock, fail = reserve_port_for_ip(Settings.bind_address, port+mask)
            if fail is not None:
                log.err("Could not reserve socket for %s (error: %s)", fail[0], fail[1])
                continue

            if port == 80:
                self.state.http_socks += [sock]
            elif port == 443:
                self.state.https_socks += [sock]

        if Settings.disable_swap:
            disable_swap()

        Settings.fix_file_permissions()
        Settings.drop_privileges()

        reactor.callLater(0, self.deferred_start)

    def shutdown(self):
        def _shutdown(_):
            self.state.orm_tp.stop()

        d = defer.Deferred()
        d.addBoth(_shutdown)

        d1 = self.state.process_supervisor.shutdown()
        d2 = self.stop_jobs()
        defer.DeferredList([d1, d2]).addCallback(d.callback)

        reactor.callLater(30, d.callback, None)

        return d

    def start_jobs(self):
        from globaleaks.jobs import jobs_list, onion_service
        from globaleaks.jobs.base import JobsMonitor

        for job in jobs_list:
            self.state.jobs.append(job())

        self.state.onion_service_job = onion_service.OnionService()
        # The only service job currently is the OnionService
        self.state.services.append(self.state.onion_service_job)

        self.state.jobs_monitor = JobsMonitor(self.state.jobs)

    def stop_jobs(self):
        deferred_list = []

        for job in self.state.jobs + self.state.services:
            deferred_list.append(job.stop())

        if self.state.jobs_monitor is not None:
            deferred_list.append(self.state.jobs_monitor.stop())
            self.state.jobs_monitor = None

        return defer.DeferredList(deferred_list)

    def _deferred_start(self):
        ret = update_db()

        if ret == -1:
            reactor.stop()
            return

        if ret == 0:
            init_db()

        sync_clean_untracked_files()
        sync_refresh_memory_variables()

        self.state.orm_tp.start()

        reactor.addSystemEventTrigger('before', 'shutdown', self.shutdown)

        for sock in self.state.http_socks:
            listen_tcp_on_sock(reactor, sock.fileno(), self.api_factory)

        self.state.process_supervisor = ProcessSupervisor(self.state.https_socks,
                                                          '127.0.0.1',
                                                          8082)

        self.state.process_supervisor.maybe_launch_https_workers()

        self.start_jobs()

        Settings.print_listening_interfaces()

    @defer.inlineCallbacks
    def deferred_start(self):
        try:
            yield self._deferred_start()
        except Exception as excep:
            fail_startup(excep)

try:
    application = service.Application('GLBackend')

    if not Settings.nodaemon and Settings.logfile:
        name = os.path.basename(Settings.logfile)
        directory = os.path.dirname(Settings.logfile)

        gl_logfile = txlogfile.LogFile(name,
                                       directory,
                                       rotateLength=Settings.log_file_size,
                                       maxRotatedFiles=Settings.num_log_files)

        application.setComponent(txlog.ILogObserver, GLLogObserver(gl_logfile).emit)

    Service().setServiceParent(application)
except Exception as excep:
    fail_startup(excep)
    # Exit with non-zero exit code to signal systemd/systemV
    sys.exit(55)
