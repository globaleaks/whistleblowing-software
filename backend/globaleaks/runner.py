# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import os

from twisted.scripts._twistd_unix import UnixApplicationRunner
from twisted.internet import reactor, defer
from twisted.python.util import untilConcludes

from globaleaks.db import init_db, clean_untracked_files, \
    refresh_memory_variables, apply_cmdline_options

from globaleaks.db.appdata import init_appdata

from globaleaks.jobs import session_management_sched, statistics_sched, \
    notification_sched, delivery_sched, cleaning_sched, \
    pgp_check_sched, mailflush_sched, secure_file_delete_sched

from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_now


def start_asynchronous_jobs():
    """
    Initialize the asynchronous operation, scheduled in the system
    """
    # Scheduled jobs will be started by reactor after reactor.run()
    #
    # Arguments to reactor.callLater do the following:
    #  - first argument is the first run delay in seconds
    #  - second argument is the function that starts the schedule
    #  - third argument is the schedule period in seconds
    session_management = session_management_sched.SessionManagementSchedule()
    reactor.callLater(0, session_management.start, GLSettings.session_management_delta)

    anomaly = statistics_sched.AnomaliesSchedule()
    reactor.callLater(0, anomaly.start, GLSettings.anomaly_delta)

    resources_check = statistics_sched.ResourcesCheckSchedule()
    reactor.callLater(0, resources_check.start, GLSettings.anomaly_delta)

    delivery = delivery_sched.DeliverySchedule()
    reactor.callLater(10, delivery.start, GLSettings.delivery_delta)

    notification = notification_sched.NotificationSchedule()
    reactor.callLater(20, notification.start, GLSettings.notification_delta)

    mailflush = mailflush_sched.MailflushSchedule()
    reactor.callLater(30, mailflush.start, GLSettings.mailflush_delta)

    secure_file_delete = secure_file_delete_sched.SecureFileDeleteSchedule()
    reactor.callLater(40, secure_file_delete.start, GLSettings.secure_file_delete_delta)

    # The Tip cleaning scheduler need to be executed every day at midnight
    current_time = datetime_now()
    delay = (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
    clean = cleaning_sched.CleaningSchedule()
    reactor.callLater(delay, clean.start, 3600 * 24)

    # The PGP check scheduler need to be executed every day at midnight
    current_time = datetime_now()
    delay = (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
    pgp_check = pgp_check_sched.PGPCheckSchedule()
    reactor.callLater(delay, pgp_check.start, 3600 * 24)

    # The Stats scheduler need to be executed every hour on the hour
    current_time = datetime_now()
    delay = (60 * 60) - (current_time.minute * 60) - current_time.second
    stats = statistics_sched.StatisticsSchedule()
    reactor.callLater(delay, stats.start, 60 * 60)


@defer.inlineCallbacks
def globaleaks_start():
    try:
        GLSettings.fix_file_permissions()
        GLSettings.drop_privileges()
        GLSettings.check_directories()

        if os.path.exists(GLSettings.db_file_path):
            yield init_appdata()
        else:
            yield init_db()

        yield clean_untracked_files()

        yield refresh_memory_variables()

        tor_configured_hosts = yield apply_cmdline_options()

        start_asynchronous_jobs()

        log.msg("GLBackend is now running")
        for ip in GLSettings.bind_addresses:
            log.msg("Visit http://%s:%d to interact with me" % (ip, GLSettings.bind_port))

        for host in GLSettings.accepted_hosts:
            if host not in GLSettings.bind_addresses:
                log.msg("Visit http://%s:%d to interact with me" % (host, GLSettings.bind_port))

        if tor_configured_hosts:
            for other in tor_configured_hosts:
                if other:
                    log.msg("Visit %s to interact with me" % other)

        log.msg("Remind: GlobaLeaks is not accessible from other URLs, this is strictly enforced")
        log.msg("Check documentation in https://github.com/globaleaks/GlobaLeaks/wiki/ for special enhancement")

    except:
        log.err("ERROR: Cannot start GlobaLeaks; please manual check the error.")
        reactor.stop()


class GLBaseRunner(UnixApplicationRunner):
    """
    This runner is specific to Unix systems.
    """
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

        reactor.callLater(0, globaleaks_start)

        self.startReactor(None, self.oldstdout, self.oldstderr)

        self.removePID(self.config['pidfile'])
