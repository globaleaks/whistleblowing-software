# -*- coding: UTF-8
#   backend
#   *******
# Here is the logic for creating a twisted service. In this part of the code we
# do all the necessary high level wiring to make everything work together.
# Specifically we create the cyclone web.Application from the API specification,
# we create a TCPServer for it and setup logging.
# We also set to kill the threadpool (the one used by Storm) when the
# application shuts down.

import os

from twisted.application import internet, service
from twisted.internet import reactor, defer
from twisted.python import log as txlog, logfile as txlogfile

from globaleaks.db import init_db, clean_untracked_files, \
    refresh_memory_variables
from globaleaks.rest import api
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, GLLogObserver
from globaleaks.utils.sock import listen_tcp_on_sock, reserve_port_for_ifaces
from globaleaks.workers.supervisor import ProcessSupervisor

# this import seems unused but it is required in order to load the mocks
import globaleaks.mocks.cyclone_mocks


class GLService(service.Service):
    def startService(self):
        if not GLSettings.nodaemon and GLSettings.logfile:
            name = os.path.basename(GLSettings.logfile)
            directory = os.path.dirname(GLSettings.logfile)

            gl_logfile = txlogfile.LogFile(name, directory,
                                         rotateLength=GLSettings.log_file_size,
                                         maxRotatedFiles=GLSettings.num_log_files)

            application.setComponent(txlog.ILogObserver, GLLogObserver(gl_logfile).emit)

        reactor.callLater(0, self.deferred_start)

    @defer.inlineCallbacks
    def _deferred_start(self):
        mask = 0
        if GLSettings.devel_mode:
            mask = 9000

        GLSettings.http_socks = []
        for port in GLSettings.bind_ports:
            port = port+mask if port < 1024 else port
            http_socks, fails = reserve_port_for_ifaces(GLSettings.bind_addresses, port)
            GLSettings.http_socks += http_socks

            for addr, err in fails:
                log.err("Could not reserve socket for %s (error: %s)" % (addr, err))

        GLSettings.https_socks, fails = reserve_port_for_ifaces(GLSettings.bind_addresses, 443+mask)
        for addr, err in fails:
            log.err("Could not reserve socket for %s (error: %s)" % (addr, err))

        GLSettings.fix_file_permissions()
        GLSettings.drop_privileges()
        GLSettings.check_directories()

        GLSettings.orm_tp.start()
        reactor.addSystemEventTrigger('after', 'shutdown', GLSettings.orm_tp.stop)

        if GLSettings.initialize_db:
            yield init_db()

        yield clean_untracked_files()

        yield refresh_memory_variables()

        GLSettings.api_factory = api.get_api_factory()

        for sock in GLSettings.http_socks:
            listen_tcp_on_sock(reactor, sock.fileno(), GLSettings.api_factory)

        GLSettings.state.process_supervisor = ProcessSupervisor(GLSettings.https_socks,
                                                                '127.0.0.1',
                                                                GLSettings.bind_port)

        yield GLSettings.state.process_supervisor.maybe_launch_https_workers()

        GLSettings.start_jobs()

        print("GlobaLeaks is now running and accessible at the following urls:")

        for ip in GLSettings.bind_addresses:
            print("- http://%s:%d%s" % (ip, GLSettings.bind_port, GLSettings.api_prefix))

        for host in GLSettings.accepted_hosts:
            if host not in GLSettings.bind_addresses:
                print("- http://%s:%d%s" % (host, GLSettings.bind_port, GLSettings.api_prefix))

        if GLSettings.tor_address is not None:
            print("- http://%s%s" % (GLSettings.tor_address, GLSettings.api_prefix))


    @defer.inlineCallbacks
    def deferred_start(self):
        try:
            yield self._deferred_start()

        except Exception as excep:
            log.err("ERROR: Cannot start GlobaLeaks; please manually check the error.")
            log.err("EXCEPTION: %s" % excep)
            reactor.stop()

application = service.Application('GLBackend')
service = GLService()
service.setServiceParent(application)
