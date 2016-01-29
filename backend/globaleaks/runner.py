# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import os

from twisted.scripts._twistd_unix import UnixApplicationRunner
from twisted.internet import reactor, defer
from twisted.python.util import untilConcludes

from globaleaks.db import check_db_files, init_db, clean_untracked_files, \
    refresh_memory_variables, apply_cmdline_options, update_version

from globaleaks.db.appdata import init_appdata

from globaleaks.jobs import session_management_sched, statistics_sched, \
    notification_sched, delivery_sched, cleaning_sched, \
    pgp_check_sched

from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_now


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
        delivery = delivery_sched.DeliverySchedule()
        self._reactor.callLater(1, delivery.start, 2)

        # Scheduling the Anomalies Check schedule to be executed every 10 seconds
        anomaly = statistics_sched.AnomaliesSchedule()
        self._reactor.callLater(0, anomaly.start, 10)

        # Scheduling the Notification schedule to be executed every 60 seconds
        notification = notification_sched.NotificationSchedule()
        self._reactor.callLater(1, notification.start, 60)

        # Scheduling the Session Management schedule to be executed every minute
        session_management = session_management_sched.SessionManagementSchedule()
        self._reactor.callLater(0, session_management.start, 60)

        # Scheduling the Tip Cleaning scheduler to be executed every day at 00:00
        current_time = datetime_now()
        delay = (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
        clean = cleaning_sched.CleaningSchedule()
        self._reactor.callLater(delay, clean.start, 3600 * 24)

        # Scheduling the PGP Check scheduler to be executed every day at 01:00
        current_time = datetime_now()
        delay = (3600 * 25) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
        pgp_check = pgp_check_sched.PGPCheckSchedule()
        self._reactor.callLater(delay, pgp_check.start, 3600 * 24)

        # Scheduling the Statistics schedule to be executed every hour on the hour
        current_time = datetime_now()
        delay = (60 * 60) - (current_time.minute * 60) - current_time.second
        stats = statistics_sched.StatisticsSchedule()
        self._reactor.callLater(delay, stats.start, 60 * 60)


    @defer.inlineCallbacks
    def start_globaleaks(self):
        try:
            GLSettings.fix_file_permissions()
            GLSettings.drop_privileges()
            GLSettings.check_directories()

            # Check presence of an existing database and eventually perform its migration
            check = check_db_files()
            if check == -1:
                 self._reactor.stop()
            elif check == 0:
                yield init_db()
            else:
                yield update_version()
                yield init_appdata()

            yield clean_untracked_files()

            yield refresh_memory_variables()

            if GLSettings.cmdline_options:
                yield apply_cmdline_options()

            self.start_asynchronous_jobs()

            log.msg("GLBackend is now running")
            for ip in GLSettings.bind_addresses:
                log.msg("Visit http://%s:%d to interact with me" % (ip, GLSettings.bind_port))

            for host in GLSettings.accepted_hosts:
                if host not in GLSettings.bind_addresses:
                    log.msg("Visit http://%s:%d to interact with me" % (host, GLSettings.bind_port))

            for other in GLSettings.configured_hosts:
                if other:
                    log.msg("Visit %s to interact with me" % other)

            log.msg("Remind: GlobaLeaks is not accessible from other URLs, this is strictly enforced")
            log.msg("Check documentation in https://github.com/globaleaks/GlobaLeaks/wiki/ for special enhancement")

        except Exception as excep:
            log.err("ERROR: Cannot start GlobaLeaks; please manual check the error.")
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
