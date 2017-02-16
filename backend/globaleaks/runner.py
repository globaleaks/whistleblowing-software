# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

from twisted.internet import reactor, defer
from twisted.scripts._twistd_unix import UnixApplicationRunner

from globaleaks.db import init_db, clean_untracked_files, \
    refresh_memory_variables
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log
from globaleaks.utils.sock import reserve_port_for_ifaces
from globaleaks.workers.supervisor import ProcessSupervisor

test_reactor = None


class GlobaLeaksRunner(UnixApplicationRunner):
    """
    This runner is specific to Unix systems.
    """
    _reactor = reactor

    def start_asynchronous_jobs(self):
        """
        Initialize the asynchronous operation, scheduled in the system
        """
        GLSettings.start_jobs()

    @defer.inlineCallbacks
    def start_globaleaks(self):
        try:
            GLSettings.fix_file_permissions()

            mask = 0
            if GLSettings.devel_mode:
                mask = 9000

            https_socks, fails = reserve_port_for_ifaces(GLSettings.bind_addresses, 443+mask)
            for addr, err in fails:
                log.err("Could not reserve socket for %s because %s!" % (addr, err))

            GLSettings.drop_privileges()
            GLSettings.check_directories()

            GLSettings.orm_tp.start()
            self._reactor.addSystemEventTrigger('after', 'shutdown', GLSettings.orm_tp.stop)

            if GLSettings.initialize_db:
                yield init_db()

            yield clean_untracked_files()

            yield refresh_memory_variables()

            GLSettings.state.process_supervisor = ProcessSupervisor(https_socks,
                                                                    '127.0.0.1',
                                                                    GLSettings.bind_port,
                                                                    GLSettings.worker_path)

            yield GLSettings.state.process_supervisor.maybe_launch_https_workers()

            self.start_asynchronous_jobs()

        except Exception as excep:
            log.err("ERROR: Cannot start GlobaLeaks; please manually check the error.")
            log.err("EXCEPTION: %s" % excep)
            self._reactor.stop()

    def postApplication(self):
        reactor.callLater(0, self.start_globaleaks)

        if test_reactor:
            self._reactor = test_reactor

        UnixApplicationRunner.postApplication(self)
