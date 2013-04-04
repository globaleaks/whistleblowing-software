# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import sys
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

from twisted.internet import reactor
from twisted.application import service, internet, app
from twisted.python.runtime import platformType
from apscheduler.scheduler import Scheduler

from globaleaks.utils import log
from globaleaks.db import create_tables, check_schema_version
from globaleaks.settings import GLSetting, transact

# The scheduler is a global variable, because can be used to force execution
__all__ = ['GLAsynchronous']

GLAsynchronous = Scheduler()

class GLBaseRunner(app.ApplicationRunner):
    """
    This is a specialized runner that is responsible for starting the specified
    service.
    The purpose of it is to do the equivalent of what would be done with
    launching twistd from command line (daemonizing the process, creating the
    PID file, etc).
    """
    def preApplication(self):
        """
        We don't actually want to override this method since there is nothing
        interesting to do in here.
        """
        log.debug("[D] %s %s " % (__file__, __name__),
                  "Class GLBaseRunner", "preApplication")

    def postApplication(self):
        """
        We must place all the operations to be done before the starting of the
        application.
        Here we will take care of the launching of the reactor and the
        operations to be done after it's shutdown.
        """
        log.debug("[D] %s %s " % (__file__, __name__),
                  "Class GLBaseRunner", "postApplication")


def start_asynchronous():
    """
    Initialize the asynchronous operation, scheduled in the system
    https://github.com/globaleaks/GLBackend/wiki/Asynchronous-and-synchronous-operation

    This method would be likely put in GLBaseRunner.postApplication, but is
    not executed by startglobaleaks.run_app, then is called by the
    OS-depenedent runner below
    """
    from globaleaks.jobs import notification_sched, statistics_sched, \
        delivery_sched, cleaning_sched

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

    deliver_sched = delivery_sched.APSDelivery()
    deliver_sched.force_execution(GLAsynchronous, seconds=5)
    GLAsynchronous.add_interval_job(deliver_sched.operation, minutes=1)

    notify_sched = notification_sched.APSNotification()
    notify_sched.force_execution(GLAsynchronous, seconds=7)
    GLAsynchronous.add_interval_job(notify_sched.operation, minutes=2)

    clean_sched = cleaning_sched.APSCleaning()
    clean_sched.force_execution(GLAsynchronous, seconds=11)
    GLAsynchronous.add_interval_job(clean_sched.operation, seconds=15)

    #stats_sched = statistics_sched.APSStatistics()
    #stats_sched.force_execution(GLAsynchronous, seconds=9)
    #GLAsynchronous.add_interval_job(stats_sched.operation, seconds=GLSetting.statistics_interval)



# System dependent runner (windows and Unix)

if platformType == "win32":

    from twisted.scripts._twistw import ServerOptions, WindowsApplicationRunner

    class GLBaseRunnerWindows(WindowsApplicationRunner):
        """
        This runner is specific to windows.
        """
        def postApplication(self):
            """
            This code is taken directly from the method postApplication of
            WindowsApplicationRunner and has not been tested
            """
            def initialization():
                if check_schema_version():
                    deferred = create_tables()
                    deferred.addCallback(run_app)
                else:
                    reactor.stop()

            def run_app(res):
                """
                Start the actual service Application.
                """

                """
                Start the actual service Application.
                """
                if not GLSetting.accepted_hosts:
                    print "Missing a list of hosts usable to contact GLBackend, abort"
                    raise AttributeError

                try:
                    service.IService(self.application).privilegedStartService()
                    app.startApplication(self.application, not self.config['no_save'])
                    app.startApplication(internet.TimerService(0.1, lambda:None), 0)
                except Exception as exc:
                    log.err("Network error: %s" % exc)
                    reactor.stop()
                    raise exc

                start_asynchronous()

                print "GLBackend is now running"
                for host in GLSetting.accepted_hosts:
                    print "Visit http://%s:%d to interact with me" % (host, GLSetting.bind_port)

            print "WARNING! Windows use has not been tested!"

            reactor.callWhenRunning(initialization)
            self.startReactor(reactor, self.oldstdout, self.oldstderr)
            log.msg("Server is shutting down.")

    GLBaseRunner = GLBaseRunnerWindows

else:
    from twisted.scripts._twistd_unix import ServerOptions, UnixApplicationRunner
    ServerOptions = ServerOptions

    class GLBaseRunnerUnix(UnixApplicationRunner):
        """
        This runner is specific to Unix systems.
        """
        def postApplication(self):

            def initialization():
                if check_schema_version():
                    deferred = create_tables()
                    return deferred.addCallback(run_app)
                else:
                    reactor.stop()
                    return None

            def run_app(res):
                """
                Start the actual service Application.
                """
                if not GLSetting.accepted_hosts:
                    print "Missing a list of hosts usable to contact GLBackend, abort"
                    raise AttributeError

                try:
                    self.startApplication(self.application)
                except Exception as exc:
                    log.err("Network error: %s" % exc)
                    reactor.stop()
                    raise exc

                start_asynchronous()

                print "GLBackend is now running"
                for host in GLSetting.accepted_hosts:
                    print "Visit http://%s:%d to interact with me" % (host, GLSetting.bind_port)

            reactor.callWhenRunning(initialization)
            self.startReactor(reactor, self.oldstdout, self.oldstderr)
            log.msg("Server is shutting down.")

    GLBaseRunner = GLBaseRunnerUnix
