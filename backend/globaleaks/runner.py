# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import os

from twisted.internet.defer import inlineCallbacks
from twisted.python.util import untilConcludes
from twisted.internet import reactor

from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now
from globaleaks.db import create_tables, check_schema_version, clean_untracked_files
from globaleaks.db.datainit import import_memory_variables, apply_cli_options
from globaleaks.settings import GLSetting

def start_asynchronous():
    """
    Initialize the asynchronous operation, scheduled in the system
    https://github.com/globaleaks/GLBackend/wiki/Asynchronous-and-synchronous-operation

    This method would be likely put in GLBaseRunner.postApplication, but is
    not executed by globaleaks.run_app, then is called by the
    OS-depenedent runner below
    """
    from globaleaks.jobs import session_management_sched, statistics_sched, \
                                notification_sched, delivery_sched, cleaning_sched, \
                                pgp_check_sched

    # Here we prepare the scheduled,
    # schedules will be started by reactor after reactor.run()
    session_management = session_management_sched.SessionManagementSchedule()
    delivery = delivery_sched.DeliverySchedule()
    notification = notification_sched.NotificationSchedule()
    clean = cleaning_sched.CleaningSchedule()
    pgp_check = pgp_check_sched.PGPCheckSchedule()

    # here we prepare the schedule:
    #  - first argument is the first run delay in seconds
    #  - second argument is the function that starts the schedule
    #  - third argument is the schedule period in seconds
    reactor.callLater(0, session_management.start, GLSetting.session_management_minutes_delta * 60)
    reactor.callLater(10, delivery.start, GLSetting.delivery_seconds_delta)
    reactor.callLater(20, notification.start, GLSetting.notification_minutes_delta * 60)
    reactor.callLater(30, clean.start, GLSetting.cleaning_hours_delta * 3600)
    reactor.callLater(60, pgp_check.start, GLSetting.pgp_check_hours_delta * 3600)


    # anti flood protection, anomaly collection, stats
    resource_check = statistics_sched.ResourceChecker()
    anomaly = statistics_sched.AnomaliesSchedule()
    stats = statistics_sched.StatisticsSchedule()

    reactor.callLater(0, resource_check.start, GLSetting.anomaly_seconds_delta)
    reactor.callLater(30, anomaly.start, GLSetting.anomaly_seconds_delta)


    # This operation, 'stats' has to be delayed (and executed in the minutes
    # of a 'clean hour', so, 01:00, 02:00, and then is repeated every 60
    # minutes.

    current_time = datetime_now()
    delay = (60 * 60) - (current_time.minute * 60) - current_time.second
    reactor.callLater( # GLSetting.stats_minutes_delta * 60,
                      # stats.start, GLSetting.stats_minutes_delta * 60)
                # more verbose approach to stats
                delay, stats.start, 60 * 60)
    statistics_sched.StatisticsSchedule.collection_start_datetime = \
        datetime_to_ISO8601(current_time)[:-8]



from twisted.scripts._twistd_unix import ServerOptions, UnixApplicationRunner
ServerOptions = ServerOptions

def globaleaks_start():

    GLSetting.fix_file_permissions()
    GLSetting.drop_privileges()
    GLSetting.check_directories()

    if not GLSetting.accepted_hosts:
        log.err("Missing a list of hosts usable to contact GLBackend, abort")
        return False

    if not check_schema_version():
        return False

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

class GLBaseRunnerUnix(UnixApplicationRunner):
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

GLBaseRunner = GLBaseRunnerUnix
