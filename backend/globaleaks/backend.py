# -*- coding: UTF-8
#   backend
#   *******
import os, sys
import traceback

from datetime import datetime

from twisted.application import internet, service
from twisted.internet import reactor, defer
from twisted.python import log as txlog, logfile as txlogfile
from twisted.web.http import _escape
from twisted.web.server import Site

from globaleaks.db import init_db, update_db, \
    sync_refresh_memory_variables, sync_clean_untracked_files
from globaleaks.rest.api import APIResourceWrapper
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, GLLogObserver
from globaleaks.utils.sock import listen_tcp_on_sock, reserve_port_for_ip
from globaleaks.workers.supervisor import ProcessSupervisor

# this import seems unused but it is required in order to load the mocks
import globaleaks.mocks.twisted_mocks


def fail_startup(excep):
    log.err("ERROR: Cannot start GlobaLeaks. Please manually examine the exception.")
    if GLSettings.nodaemon and GLSettings.devel_mode:
        print("EXCEPTION: %s" %  traceback.format_exc(excep))
    else:
        log.err("EXCEPTION: %s" %  excep)
    if reactor.running:
        reactor.stop()


def pre_listen_startup():
    mask = 0
    if GLSettings.devel_mode:
        mask = 9000

    GLSettings.http_socks = []
    for port in GLSettings.bind_ports:
        port = port+mask if port < 1024 else port
        http_sock, fail = reserve_port_for_ip(GLSettings.bind_address, port)
        if fail is not None:
            log.err("Could not reserve socket for %s (error: %s)" % (fail[0], fail[1]))
        else:
            GLSettings.http_socks += [http_sock]

    https_sock, fail = reserve_port_for_ip(GLSettings.bind_address, 443+mask)
    if fail is not None:
        log.err("Could not reserve socket for %s (error: %s)" % (fail[0], fail[1]))
    else:
        GLSettings.https_socks = [https_sock]

    GLSettings.fix_file_permissions()
    GLSettings.drop_privileges()
    GLSettings.check_directories()

def timedLogFormatter(timestamp, request):
    duration = -1
    if hasattr(request, 'start_time'):
        duration = round((datetime.now() - request.start_time).microseconds / 1000, 4)

    line = (u'%(code)s %(method)s %(uri)s %(length)s %(duration)dms' % dict(
              duration=duration,
              method=_escape(request.method),
              uri=_escape(request.uri),
              proto=_escape(request.clientproto),
              code=request.code,
              length=request.sentLength or u"-"))

    return line


class GLService(service.Service):
    def startService(self):
        reactor.callLater(0, self.deferred_start)

    @defer.inlineCallbacks
    def deferred_start(self):
        try:
            yield self._deferred_start()
        except Exception as excep:
            fail_startup(excep)

    @defer.inlineCallbacks
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

        GLSettings.state.process_supervisor = ProcessSupervisor(GLSettings.https_socks,
                                                                '127.0.0.1',
                                                                GLSettings.bind_port)

        yield GLSettings.state.process_supervisor.maybe_launch_https_workers()

        GLSettings.start_jobs()

        print("GlobaLeaks is now running and accessible at the following urls:")

        if GLSettings.memory_copy.reachable_via_web:
            print("- http://%s:%d%s" % (GLSettings.bind_address, GLSettings.bind_port, GLSettings.api_prefix))
            if GLSettings.memory_copy.hostname:
                print("- http://%s:%d%s" % (GLSettings.memory_copy.hostname, GLSettings.bind_port, GLSettings.api_prefix))
        else:
            print("- http://127.0.0.1:%d%s" % (GLSettings.bind_port, GLSettings.api_prefix))

        if GLSettings.memory_copy.onionservice != '':
            print("- http://%s%s" % (GLSettings.memory_copy.onionservice, GLSettings.api_prefix))


application = service.Application('GLBackend')

if not GLSettings.nodaemon and GLSettings.logfile:
    name = os.path.basename(GLSettings.logfile)
    directory = os.path.dirname(GLSettings.logfile)

    gl_logfile = txlogfile.LogFile(name, directory,
                                 rotateLength=GLSettings.log_file_size,
                                 maxRotatedFiles=GLSettings.num_log_files)

    application.setComponent(txlog.ILogObserver, GLLogObserver(gl_logfile).emit)

try:
    pre_listen_startup()

    service = GLService()
    service.setServiceParent(application)

except Exception as excep:
    fail_startup(excep)
    # Exit with non-zero exit code to signal systemd/system5
    sys.exit(55)
