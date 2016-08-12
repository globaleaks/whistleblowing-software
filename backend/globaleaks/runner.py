# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import os

from twisted.scripts._twistd_unix import UnixApplicationRunner
from twisted.internet import reactor, defer
from twisted.python.util import untilConcludes

from globaleaks.db import init_db, clean_untracked_files, \
    refresh_memory_variables, handle_stored_version

from globaleaks.db.appdata import update_appdata

from globaleaks.jobs import session_management_sched, statistics_sched, \
    notification_sched, delivery_sched, cleaning_sched, \
    pgp_check_sched

from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_now, disable_swap


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

        # Scheduling the Delivery schedule to be executed every 2 seconds
        delivery_sched.DeliverySchedule().schedule(2, 1)

        # Scheduling the Anomalies Check schedule to be executed every 30 seconds
        statistics_sched.AnomaliesSchedule().schedule(30, 2)

        # Scheduling the Notification schedule to be executed every 60 seconds
        notification_sched.NotificationSchedule().schedule(60, 3)

        # Scheduling the Session Management schedule to be executed every minute
        session_management_sched.SessionManagementSchedule().schedule(60, 5)

        # Scheduling the Tip Cleaning scheduler to be executed every day at 00:00
        current_time = datetime_now()
        delay = (3600 * (24 + 0)) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
        clean = cleaning_sched.CleaningSchedule().schedule(3600 * 24, delay)

        # Scheduling the PGP Check scheduler to be executed every day at 02:00
        delay = (3600 * (24 + 2)) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
        pgp_check = pgp_check_sched.PGPCheckSchedule().schedule(3600 * 24, delay)

        # Scheduling the Statistics schedule to be executed every hour on the hour
        delay = (3600) - (current_time.minute * 60) - current_time.second
        stats = statistics_sched.StatisticsSchedule().schedule(3600, delay)

    @defer.inlineCallbacks
    def start_globaleaks(self):
        try:
            GLSettings.fix_file_permissions()
            GLSettings.drop_privileges()
            GLSettings.check_directories()

            if GLSettings.initialize_db:
                yield init_db()
            else:
                yield handle_stored_version()

            yield clean_untracked_files()

            yield refresh_memory_variables()

            self.start_asynchronous_jobs()

        except Exception as excep:
            log.err("ERROR: Cannot start GlobaLeaks; please manually check the error.")
            log.err("EXCEPTION: %s" % excep)
            self._reactor.stop()

    def postApplication(self):
        """
        Run the application.
        """
        try:
            self.startApplication(self.application)
        except Exception as ex:
            statusPipe = self.config.get("statusPipe", None)
            if statusPipe is not None:
                # Limit the total length to the passed string to 100
                strippedError = str(ex)[:98]
                untilConcludes(os.write, statusPipe, "1 %s" % (strippedError,))
                untilConcludes(os.close, statusPipe)
            self.removePID(self.config['pidfile'])
            raise
        else:
            statusPipe = self.config.get("statusPipe", None)
            if statusPipe is not None:
                untilConcludes(os.write, statusPipe, "0")
                untilConcludes(os.close, statusPipe)

        self._reactor.callLater(0, self.start_globaleaks)

        self.startReactor(None, self.oldstdout, self.oldstderr)

        self.removePID(self.config['pidfile'])
