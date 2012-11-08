# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from twisted.python import log
from twisted.application import service, internet, app
from twisted.python.runtime import platformType

from globaleaks.db import createTables

# same name mistake = shit,
# log appears to not be used, but is called as log.debug
from globaleaks.utils import log
# XXX

# The scheduler is a global variable, because can be used to force execution
GLAsynchronous = None

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
        log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunner", "preApplication")
        pass

    def postApplication(self):
        """
        We must place all the operations to be done before the starting of the
        application.
        Here we will take care of the launching of the reactor and the
        operations to be done after it's shutdown.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunner", "postApplication")
        pass


def startAsynchronous():
    """
    Initialize the asynchronous operation, scheduled in the system
    https://github.com/globaleaks/GLBackend/wiki/Asynchronous-and-synchronous-operations

    This method would be likely put in GLBaseRunner.postApplication, but is not executed by
    startglobaleaks.runApp, then is called by the OS-depenedent runner below
    """
    from apscheduler.scheduler import Scheduler
    from globaleaks.jobs import notification_sched, statistics_sched, tip_sched, \
        delivery_sched, cleaning_sched, welcome_sched, digest_sched

    GLAsynchronous = Scheduler()
    # When the application boot, maybe because has been restarted. then, execute all the
    # periodic operation by hand.

    StatsSched = statistics_sched.APSStatistics()
    StatsSched.force_execution(GLAsynchronous, seconds=10)
    GLAsynchronous.add_interval_job(StatsSched.operation, StatsSched.get_node_delta() )

    WelcomSched = welcome_sched.APSWelcome()
    WelcomSched.force_execution(GLAsynchronous, seconds=15)
    GLAsynchronous.add_interval_job(WelcomSched.operation, minutes=5)

    TipSched = tip_sched.APSTip()
    TipSched.force_execution(GLAsynchronous, seconds=20)
    GLAsynchronous.add_interval_job(TipSched.operation, minutes=1)

    # TODO - InputFilter processing, before considering a Folder safe, need
    #        to be scheduler and then would be 'data available' for delivery

    DeliverSched = delivery_sched.APSDelivery()
    DeliverSched.force_execution(GLAsynchronous, seconds=25)
    GLAsynchronous.add_interval_job(DeliverSched.operation, minutes=2)

    NotifSched = notification_sched.APSNotification()
    NotifSched.force_execution(GLAsynchronous, seconds=30)
    GLAsynchronous.add_interval_job(NotifSched.operation, minutes=3)

    CleanSched = cleaning_sched.APSCleaning()
    CleanSched.force_execution(GLAsynchronous, seconds=35)
    GLAsynchronous.add_interval_job(CleanSched.operation, hours=6)
    # TODO not hours=6 but CleanSched.get_contexts_policies()

    DigestSched = digest_sched.APSDigest()
    GLAsynchronous.add_interval_job(DigestSched.operation, minutes=10)
    # TODO not minutes=10 but DigestSched.get_context_policies()
    # TODO digest is a system-library-like

    # start the scheduler
    GLAsynchronous.start()


# System dependent runner (windows and Unix)

if platformType == "win32":

    from twisted.scripts._twistw import ServerOptions, WindowsApplicationRunner

    class GLBaseRunnerWindows(WindowsApplicationRunner):
        """
        This runner is specific to windows.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunnerWindows")
        def postApplication(self):
            """
            This code is taken directly from the method postApplication of
            WindowsApplicationRunner.
            """
            log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunnerWindows", "postApplication")
            def runApp(res):
                """
                Start the actual service Application.
                """
                log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunner", "preApplication", "runApp")
                service.IService(self.application).privilegedStartService()
                app.startApplication(self.application, not self.config['no_save'])
                app.startApplication(internet.TimerService(0.1, lambda:None), 0)
                startAsynchronous()

            print "WARNING! Windows is not tested!"
            d = createTables()
            d.addCallback(runApp)

            self.startReactor(None, self.oldstdout, self.oldstderr)
            log.msg("Server Shut Down.")

    GLBaseRunner = GLBaseRunnerWindows

else:

    from twisted.scripts._twistd_unix import ServerOptions, UnixApplicationRunner
    ServerOptions = ServerOptions

    class GLBaseRunnerUnix(UnixApplicationRunner):
        """
        This runner is specific to Unix systems.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunnerUnix")
        def postApplication(self):
            """
            THis code is taken directly from UnixApplicationRunner
            """
            log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunnerUnix", "postApplication")
            def runApp(res):
                """
                Start the actual service Application.
                """
                log.debug("[D] %s %s " % (__file__, __name__), "Class GLBaseRunnerUnix", "postApplication", "runApp")
                print "Running start."
                self.startApplication(self.application)
                startAsynchronous()
                print "GLBackend is now running"
                print "Visit http://127.0.0.1:8082/index.html to interact with me"

            d = createTables()
            d.addBoth(runApp)

            self.startReactor(None, self.oldstdout, self.oldstderr)
            self.removePID(self.config['pidfile'])

    GLBaseRunner = GLBaseRunnerUnix

GLBaseRunner.loggerFactory = log.LoggerFactory

