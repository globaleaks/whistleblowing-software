# -*- coding: utf-8
#   backend
#   *******
import sys
import traceback

from twisted.application import service
from twisted.internet import reactor, defer
from twisted.python.log import ILogObserver
from twisted.web import resource, server

from globaleaks.jobs import job, jobs_list
from globaleaks.services import onion

from globaleaks.db import create_db, init_db, update_db, \
    sync_refresh_memory_variables, sync_clean_untracked_files, sync_initialize_snimap
from globaleaks.rest.api import APIResourceWrapper
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.log import log, openLogFile, logFormatter, LogObserver
from globaleaks.utils.process import drop_privileges, set_proc_title
from globaleaks.utils.sock import listen_tcp_on_sock, listen_tls_on_sock, reserve_port_for_ip
from globaleaks.utils.utility import fix_file_permissions


def fail_startup(excep):
    log.err("ERROR: Cannot start GlobaLeaks. Please manually examine the exception.")
    log.err("EXCEPTION: %s", excep)
    log.debug('TRACE: %s', traceback.format_exc(excep))
    if reactor.running:
        reactor.stop()


class Request(server.Request):
    session = None
    log_ip_and_ua = False


class Site(server.Site):
    requestFactory = Request

    def _openLogFile(self, path):
        return openLogFile(path, Settings.log_file_size, Settings.num_log_files)


class Service(service.Service):
    _shutdown = False

    def __init__(self):
        set_proc_title('globaleaks')

        self.state = State
        self.arw = resource.EncodingResourceWrapper(APIResourceWrapper(), [server.GzipEncoderFactory()])

        if Settings.nodaemon:
            self.api_factory = Site(self.arw, logFormatter=logFormatter)
        else:
            self.api_factory = Site(self.arw, logPath=Settings.accesslogfile, logFormatter=logFormatter)

        self.api_factory.displayTracebacks = False

    def startService(self):
        mask = 0
        if Settings.devel_mode:
            mask = 8000

        # Allocate local ports
        for port in Settings.bind_local_ports:
            http_sock, fail = reserve_port_for_ip('127.0.0.1', port)
            if fail is not None:
                log.err("Could not reserve socket for %s (error: %s)",
                        fail.args[0], fail.args[1])
            else:
                self.state.http_socks += [http_sock]

        # Allocate remote ports
        for port in Settings.bind_remote_ports:
            sock, fail = reserve_port_for_ip(Settings.bind_address, port+mask)
            if fail is not None:
                log.err("Could not reserve socket for %s (error: %s)",
                        fail.args[0], fail.args[1])
                continue

            if port == 80:
                self.state.http_socks += [sock]
            elif port == 443:
                self.state.https_socks += [sock]

        fix_file_permissions(Settings.working_path,
                             Settings.uid,
                             Settings.gid,
                             0o700,
                             0o600)

        drop_privileges(Settings.user, Settings.uid, Settings.gid)

        reactor.callLater(0, self.deferred_start)

    def shutdown(self):
        d = defer.Deferred()

        def _shutdown(_):
            if self._shutdown:
                return

            self._shutdown = True
            self.state.orm_tp.stop()
            d.callback(None)

        reactor.callLater(30, _shutdown, None)

        self.stop_jobs().addBoth(_shutdown)

        return d

    def start_jobs(self):
        for j in jobs_list:
            self.state.jobs.append(j())

        self.state.onion_service_job = onion.OnionService()
        # The only service job currently is the OnionService
        self.state.services.append(self.state.onion_service_job)

        self.state.jobs_monitor = job.JobsMonitor(self.state.jobs)

    def stop_jobs(self):
        deferred_list = []

        for job in self.state.jobs + self.state.services:
            deferred_list.append(defer.maybeDeferred(job.stop))

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
            create_db()
            init_db()

        sync_clean_untracked_files()
        sync_refresh_memory_variables()
        sync_initialize_snimap()

        self.state.orm_tp.start()

        reactor.addSystemEventTrigger('before', 'shutdown', self.shutdown)

        for sock in self.state.http_socks:
            listen_tcp_on_sock(reactor, sock.fileno(), self.api_factory)

        for sock in self.state.https_socks:
            listen_tls_on_sock(reactor,
                               fd=sock.fileno(),
                               contextFactory=self.state.snimap,
                               factory=self.api_factory)

        self.start_jobs()

        self.print_listening_interfaces()

    @defer.inlineCallbacks
    def deferred_start(self):
        try:
            yield self._deferred_start()
        except Exception as excep:
            fail_startup(excep)

    def print_listening_interfaces(self):
        print("GlobaLeaks is now running and accessible at the following urls:")

        tenant_cache = self.state.tenant_cache[1]

        if self.state.settings.devel_mode:
            print("- [HTTP]\t--> http://127.0.0.1:8082")

        elif self.state.tenant_cache[1].reachable_via_web:
            hostname = tenant_cache.hostname if tenant_cache.hostname else '0.0.0.0'
            print("- [HTTP]\t--> http://%s" % hostname)
            if tenant_cache.https_enabled:
                print("- [HTTPS]\t--> https://%s" % hostname)

        if tenant_cache.onionservice:
            print("- [Tor]:\t--> http://%s" % tenant_cache.onionservice)


try:
    application = service.Application('GlobaLeaks')

    if not Settings.nodaemon:
        logfile = openLogFile(Settings.logfile, Settings.log_file_size, Settings.num_log_files)
        application.setComponent(ILogObserver, LogObserver(logfile).emit)

    Service().setServiceParent(application)
except Exception as excep:
    fail_startup(excep)
    # Exit with non-zero exit code to signal systemd/systemV
    sys.exit(55)
