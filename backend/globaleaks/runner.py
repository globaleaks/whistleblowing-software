# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import os

from twisted.scripts._twistd_unix import UnixApplicationRunner
from twisted.internet.defer import inlineCallbacks
from twisted.python.util import untilConcludes
from twisted.internet import reactor

from globaleaks.db import create_tables, clean_untracked_files, check_schema_version
from globaleaks.db.datainit import import_memory_variables, apply_cli_options

from globaleaks.jobs import session_management_sched, statistics_sched, \
    notification_sched, delivery_sched, cleaning_sched, \
    pgp_check_sched, mailflush_sched

from globaleaks.settings import GLSetting
from globaleaks.utils.utility import log, datetime_now

def start_asynchronous():
    """
    Initialize the asynchronous operation, scheduled in the system
    """
    # Here we prepare the scheduled,
    # schedules will be started by reactor after reactor.run()
    session_management = session_management_sched.SessionManagementSchedule()
    delivery = delivery_sched.DeliverySchedule()
    notification = notification_sched.NotificationSchedule()
    clean = cleaning_sched.CleaningSchedule()
    pgp_check = pgp_check_sched.PGPCheckSchedule()
    mailflush = mailflush_sched.MailflushSchedule()
    resource_check = statistics_sched.ResourceChecker()
    anomaly = statistics_sched.AnomaliesSchedule()
    stats = statistics_sched.StatisticsSchedule()

    # here we prepare the schedule:
    #  - first argument is the first run delay in seconds
    #  - second argument is the function that starts the schedule
    #  - third argument is the schedule period in seconds
    reactor.callLater(0, session_management.start, GLSetting.session_management_minutes_delta * 60)
    reactor.callLater(0, anomaly.start, GLSetting.anomaly_seconds_delta)
    reactor.callLater(0, resource_check.start, GLSetting.anomaly_seconds_delta)

    # reactor.callLater(10, delivery.start, GLSetting.delivery_seconds_delta)
    reactor.callLater(1, delivery.start, 2)
    # Test, End2End, fast delivery.

    reactor.callLater(20, notification.start, GLSetting.notification_minutes_delta * 60)
    reactor.callLater(40, mailflush.start, GLSetting.mailflush_minutes_delta * 60)

    # The Tip cleaning scheduler need to be executed every day at midnight
    current_time = datetime_now()
    delay = (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
    reactor.callLater(delay, clean.start, 3600 * 24)

    # The PGP check scheduler need to be executed every day at midnight
    current_time = datetime_now()
    delay = (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second
    reactor.callLater(delay, pgp_check.start, 3600 * 24)

    # The Stats scheduler need to be executed every hour on the hour
    current_time = datetime_now()
    delay = (60 * 60) - (current_time.minute * 60) - current_time.second
    reactor.callLater(delay, stats.start, 60 * 60)
    statistics_sched.StatisticsSchedule.collection_start_datetime = current_time


def globaleaks_start():
    GLSetting.fix_file_permissions()
    GLSetting.drop_privileges()
    GLSetting.check_directories()

    if not GLSetting.accepted_hosts:
        log.err("Missing a list of hosts usable to contact GLBackend, abort")
        return False

    # return False do not make globaleaks abort, this is an issue
    #if not check_schema_version():
    #    return False

    d = create_tables()

    d.addCallback(clean_untracked_files)

    @d.addCallback
    @inlineCallbacks
    def cb(res):
        start_asynchronous()
        yield import_memory_variables()
        tor_configured_hosts = yield apply_cli_options()

        log.msg("GLBackend is now running")
        for ip in GLSetting.bind_addresses:
            log.msg("Visit http://%s:%d to interact with me" % (ip, GLSetting.bind_port))

        for host in GLSetting.accepted_hosts:
            if host not in GLSetting.bind_addresses:
                log.msg("Visit http://%s:%d to interact with me" % (host, GLSetting.bind_port))

        if tor_configured_hosts:
            for other in tor_configured_hosts:
                if other:
                    log.msg("Visit %s to interact with me" % other)

        log.msg("Remind: GlobaLeaks is not accessible from other URLs, this is strictly enforced")
        log.msg("Check documentation in https://github.com/globaleaks/GlobaLeaks/wiki/ for special enhancement")

    return True

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

        if globaleaks_start():
            self.startReactor(None, self.oldstdout, self.oldstderr)
        else:
            log.err("Cannot start GlobaLeaks; please manual check the error.")
            quit(-1)

        self.removePID(self.config['pidfile'])
