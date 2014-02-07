# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import os

from twisted.internet.defer import inlineCallbacks
from twisted.python.util import untilConcludes

from apscheduler.scheduler import Scheduler

from globaleaks.utils.utility import log, utc_future_date
from globaleaks.db import create_tables, check_schema_version
from globaleaks.db.datainit import import_memory_variables, apply_cli_options
from globaleaks.settings import GLSetting

# The scheduler is a global variable, because can be used to force execution
__all__ = ['GLAsynchronous']

GLAsynchronous = Scheduler()

def start_asynchronous():
    """
    Initialize the asynchronous operation, scheduled in the system
    https://github.com/globaleaks/GLBackend/wiki/Asynchronous-and-synchronous-operation

    This method would be likely put in GLBaseRunner.postApplication, but is
    not executed by globaleaks.run_app, then is called by the
    OS-depenedent runner below
    """
    from globaleaks.jobs import session_management_sched, statistics_sched, \
                                notification_sched, delivery_sched, cleaning_sched

    # When the application boot, maybe because has been after a restart, then
    # with the method *.force_execution, we reschedule the execution of all the
    # operations

    # start the scheduler, before add the Schedule job
    GLAsynchronous.start()

    # This maybe expanded for debug:
    # def event_debug_listener(event):
    #     if event.exception:
    #         Job failed
    #     else:
    #         Job success
    #         GLAsynchronous.print_jobs()
    # GLAsynchronous.add_listener(event_debug_listener,
    #       EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED)

    session_manage_sched = session_management_sched.APSSessionManagement()
    GLAsynchronous.add_interval_job(session_manage_sched.operation,
                                    minutes=GLSetting.session_management_minutes_delta,
                                    start_date=utc_future_date(seconds=3))

    deliver_sched = delivery_sched.APSDelivery()
    GLAsynchronous.add_interval_job(deliver_sched.operation,
                                    seconds=GLSetting.delivery_seconds_delta,
                                    start_date=utc_future_date(seconds=5))

    notify_sched = notification_sched.APSNotification()
    GLAsynchronous.add_interval_job(notify_sched.operation,
                                    minutes=GLSetting.notification_minutes_delta,
                                    start_date=utc_future_date(seconds=7))

    clean_sched = cleaning_sched.APSCleaning()
    GLAsynchronous.add_interval_job(clean_sched.operation,
                                    hours=GLSetting.cleaning_hours_delta,
                                    start_date=utc_future_date(seconds=10))

    # expiration_sched = gpgexpire_sched.GPGExpireCheck()
    # GLAsynchronous.add_interval_job(expiration_sched.operation,
    #                                 hours=23,
    #                                 start_date=utc_future_date(seconds=50))

    anomaly_sched = statistics_sched.APSAnomalies()
    GLAsynchronous.add_interval_job(anomaly_sched.operation,
                                    minutes=GLSetting.anomaly_seconds_delta)

    stats_sched = statistics_sched.APSStatistics()
    GLAsynchronous.add_interval_job(stats_sched.operation,
                                    minutes=GLSetting.stats_minutes_delta)


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
