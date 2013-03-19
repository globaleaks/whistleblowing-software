# -*- encoding: utf-8 -*-
#
# Here is implemented the preApplication and postApplication method
# along the Asynchronous event schedule

import sys

from twisted.internet import reactor
from twisted.application import service, internet, app
from twisted.python.runtime import platformType
from apscheduler.scheduler import Scheduler

from globaleaks.db import create_tables
from globaleaks.utils import log, mail_exception
from globaleaks.settings import GLSetting

# The scheduler is a global variable, because can be used to force execution
__all__ = ['GLAsynchronous']

GLAsynchronous = Scheduler()
log.start_logging()

sys.excepthook = mail_exception

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
    # operations -- TODO, maybe refactored along the scheduler review in TODO

    stats_sched = statistics_sched.APSStatistics()
    stats_sched.force_execution(GLAsynchronous, seconds=8)
    GLAsynchronous.add_interval_job(stats_sched.operation, 10 )
    # TODO GLAsynchronous.add_interval_job(StatsSched.operation, StatsSched.get_node_delta() )

    deliver_sched = delivery_sched.APSDelivery()
    deliver_sched.force_execution(GLAsynchronous, seconds=1)
    GLAsynchronous.add_interval_job(deliver_sched.operation, seconds=7)

    notify_sched = notification_sched.APSNotification()
    notify_sched.force_execution(GLAsynchronous, seconds=5)
    GLAsynchronous.add_interval_job(notify_sched.operation, minutes=3)

    clean_sched = cleaning_sched.APSCleaning()
    clean_sched.force_execution(GLAsynchronous, seconds=13)
    GLAsynchronous.add_interval_job(clean_sched.operation, hours=6)
    # TODO not hours=6 but CleanSched.get_contexts_policies()

    # start the scheduler
    GLAsynchronous.start()


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
            WindowsApplicationRunner.
            """
            def initialization():
                deferred = create_tables()
                deferred.addCallback(run_app)

            def run_app(res):
                """
                Start the actual service Application.
                """
                service.IService(self.application).privilegedStartService()
                app.startApplication(self.application, not self.config['no_save'])
                app.startApplication(internet.TimerService(0.1, lambda:None), 0)
                start_asynchronous()

            print "WARNING! Windows use has not been tested!"

            reactor.callWhenRunning(initialization)
            self.startReactor(None, self.oldstdout, self.oldstderr)
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
            """
            THis code is taken directly from UnixApplicationRunner
            """
            def initialization():
                deferred = create_tables()
                deferred.addCallback(run_app)

            def run_app(res):
                """
                Start the actual service Application.
                """
                print "Running start."
                if not GLSetting.accepted_hosts:
                    print "Missing a list of hosts usable to contact GLBackend, abort"
                    raise AttributeError

                try:
                    self.startApplication(self.application)
                except Exception, exc:
                    log.err("Network error: %s" % exc)
                    reactor.stop()
                    raise exc

                try:
                    start_asynchronous()
                except Exception, exc:
                    log.err("Scheduler error: %s" % exc)
                    reactor.stop()
                    raise exc

                print "GLBackend is now running"
                for host in GLSetting.accepted_hosts:
                    print "Visit http://%s:%d to interact with me" % (host, GLSetting.bind_port)

            reactor.callWhenRunning(initialization)
            self.startReactor(reactor, self.oldstdout, self.oldstderr)
            log.msg("Server is shutting down.")
            self.removePID(self.config['pidfile'])

    GLBaseRunner = GLBaseRunnerUnix
