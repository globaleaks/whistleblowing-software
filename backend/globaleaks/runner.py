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
from globaleaks.utils.http_master import ProcessSupervisor
from globaleaks.utils.sock import reserve_network_sockets

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

            public_net_sockets = reserve_network_sockets(mask=9000)

            GLSettings.drop_privileges()
            GLSettings.check_directories()

            GLSettings.orm_tp.start()
            self._reactor.addSystemEventTrigger('after', 'shutdown', GLSettings.orm_tp.stop)

            if GLSettings.initialize_db:
                yield init_db()

            yield clean_untracked_files()

            yield refresh_memory_variables()

            self.start_asynchronous_jobs()

            GLSettings.state.process_supervisor = ProcessSupervisor(public_net_sockets)

            yield GLSettings.state.process_supervisor.maybe_launch_https_workers()

        except Exception as excep:
            log.err("ERROR: Cannot start GlobaLeaks; please manually check the error.")
            log.err("EXCEPTION: %s" % excep)
            self._reactor.stop()

    def postApplication(self):
        reactor.callLater(0, self.start_globaleaks)

        if test_reactor:
            self._reactor = test_reactor

        UnixApplicationRunner.postApplication(self)
