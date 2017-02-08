# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

from twisted.internet import reactor, defer
from twisted.scripts._twistd_unix import UnixApplicationRunner

from globaleaks.db import init_db, clean_untracked_files, \
    refresh_memory_variables
from globaleaks.jobs import jobs_list
from globaleaks.jobs.base import GLJobsMonitor
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log

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
        if test_reactor:
            self._reactor = test_reactor

        jobs = []
        for job in jobs_list:
            j = job()
            j.schedule()
            jobs.append(j)

        monitor = GLJobsMonitor(jobs)
        monitor.schedule()

    @defer.inlineCallbacks
    def start_globaleaks(self):
        try:
            GLSettings.fix_file_permissions()
            GLSettings.drop_privileges()
            GLSettings.check_directories()

            GLSettings.orm_tp.start()
            self._reactor.addSystemEventTrigger('after', 'shutdown', GLSettings.orm_tp.stop)

            if GLSettings.initialize_db:
                yield init_db()

            yield clean_untracked_files()

            yield refresh_memory_variables()

            self.start_asynchronous_jobs()

        except Exception as excep:
            log.err("ERROR: Cannot start GlobaLeaks; please manually check the error.")
            log.err("EXCEPTION: %s" % excep)
            self._reactor.stop()

    def postApplication(self):
        reactor.callLater(0, self.start_globaleaks)

        UnixApplicationRunner.postApplication(self)
