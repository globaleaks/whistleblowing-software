# -*- coding: UTF-8
#   backend
#   *******
import os, sys
import traceback

from datetime import datetime

from twisted.application import service
from twisted.internet import reactor, defer
from twisted.python import log as txlog, logfile as txlogfile
from twisted.web.http import _escape
from twisted.web.server import Site

from globaleaks.db import init_db, update_db, \
    sync_refresh_memory_variables, sync_clean_untracked_files
from globaleaks.rest.api import APIResourceWrapper
from globaleaks.settings import GLSettings
from globaleaks.utils.process import disable_swap
from globaleaks.utils.sock import listen_tcp_on_sock, reserve_port_for_ip
from globaleaks.utils.utility import log, timedelta_to_milliseconds, GLLogObserver
from globaleaks.workers.supervisor import ProcessSupervisor

# this import seems unused but it is required in order to load the mocks
import globaleaks.mocks.twisted_mocks


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


class GLService(service.Service):
    def startService(self):
        mask = 0
        if GLSettings.devel_mode:
            mask = 8000

        GLSettings.http_socks = []

        # Allocate local ports
        for port in GLSettings.bind_local_ports:
            http_sock, fail = reserve_port_for_ip('127.0.0.1', port)
            if fail is not None:
                log.err("Could not reserve socket for %s (error: %s)", fail[0], fail[1])
            else:
                GLSettings.http_socks += [http_sock]

        # Allocate remote ports
        for port in GLSettings.bind_remote_ports:
            sock, fail = reserve_port_for_ip(GLSettings.bind_address, port+mask)
            if fail is not None:
                log.err("Could not reserve socket for %s (error: %s)", fail[0], fail[1])
                continue

            if port == 80:
                GLSettings.http_socks += [sock]
            elif port == 443:
                GLSettings.https_socks += [sock]

        if GLSettings.disable_swap:
            disable_swap()

        GLSettings.fix_file_permissions()
        GLSettings.drop_privileges()
        GLSettings.check_directories()

        reactor.callLater(0, self.deferred_start)

    @defer.inlineCallbacks
    def deferred_start(self):
        try:
            yield self._deferred_start()
        except Exception as excep:
            fail_startup(excep)

    def _deferred_start(self):
        ret = update_db()

        if ret == -1:
            reactor.stop()

        if ret == 0:
            init_db()

        sync_clean_untracked_files()
        sync_refresh_memory_variables()

        GLSettings.orm_tp.start()

        reactor.addSystemEventTrigger('after', 'shutdown', GLSettings.orm_tp.stop)

        arw = APIResourceWrapper()

        GLSettings.api_factory = Site(arw, logFormatter=timedLogFormatter)

        for sock in GLSettings.http_socks:
            listen_tcp_on_sock(reactor, sock.fileno(), GLSettings.api_factory)

        GLSettings.appstate.process_supervisor = ProcessSupervisor(GLSettings.https_socks,
                                                                '127.0.0.1',
                                                                8082)

        GLSettings.appstate.process_supervisor.maybe_launch_https_workers()

        GLSettings.start_jobs()
        GLSettings.start_services()

        GLSettings.print_listening_interfaces()


application = service.Application('GLBackend')

if not GLSettings.nodaemon and GLSettings.logfile:
    name = os.path.basename(GLSettings.logfile)
    directory = os.path.dirname(GLSettings.logfile)

    gl_logfile = txlogfile.LogFile(name, directory,
                                 rotateLength=GLSettings.log_file_size,
                                 maxRotatedFiles=GLSettings.num_log_files)

    application.setComponent(txlog.ILogObserver, GLLogObserver(gl_logfile).emit)

try:
    GLService().setServiceParent(application)
except Exception as excep:
    fail_startup(excep)
    # Exit with non-zero exit code to signal systemd/systemV
    sys.exit(55)
