# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks
import exceptions
import sys
import time

from twisted.internet import task, defer, reactor
from twisted.python.failure import Failure

from globaleaks.handlers.base import TimingStatsHandler
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import mail_exception_handler, send_exception_email
from globaleaks.utils.utility import log


test_reactor = None


DEFAULT_JOB_MONITOR_TIME = 5 * 60 # seconds


class GLJob(task.LoopingCall):
    name = "unnamed"
    iterations = 0
    start_time = 0
    mean_time = -1
    low_time = -1
    high_time = -1

    monitor = None
    monitor_time = DEFAULT_JOB_MONITOR_TIME

    def __init__(self):
        task.LoopingCall.__init__(self, self._operation)
        self.clock = reactor if test_reactor is None else test_reactor

    def stats_collection_start(self):
        self.run = 0

        self.start_time = time.time()

        if self.mean_time != -1:
            log.time_debug("Starting job [%s] expecting an execution time of %.4f [low: %.4f, high: %.4f]" %
                      (self.name, self.mean_time, self.low_time, self.high_time))
        else:
            log.time_debug("Starting job [%s]" % self.name)

        def monitor_fun(self):
            self.run += 1
            elapsed_time = self.monitor_time * self.run

            if elapsed_time < 60:
                error = "Warning: [%s] is taking more than %d seconds to execute" % (self.name, elapsed_time)
            elif elapsed_time < 3600:
                minutes = int(elapsed_time / 60)
                error = "Warning: [%s] is taking more than %d minutes to execute" % (self.name, minutes)
            else:
                hours = int(elapsed_time / 3600)
                error = "Warning: [%s] is taking more than %d hours to execute" % (self.name, hours)

            log.err(error)
            send_exception_email(error, mail_reason="Job Time Exceeded")

        self.monitor = task.LoopingCall(monitor_fun, self)
        self.monitor.start(self.monitor_time, False)

    def stats_collection_end(self):
        if self.monitor is not None:
            try:
                self.monitor.stop()
            except:
                pass
            finally:
                self.monitor = None

        current_run_time = time.time() - self.start_time

        # discard empty cicles from stats
        if current_run_time > 0.000000:
            self.mean_time = ((self.mean_time * self.iterations) + current_run_time) / (self.iterations + 1)

        if self.low_time == -1 or current_run_time < self.low_time:
            self.low_time = current_run_time

        if self.high_time == -1 or current_run_time > self.high_time:
            self.high_time = current_run_time

        log.time_debug("Ended job [%s] with an execution time of %.4f seconds" % (self.name, current_run_time))

        self.iterations += 1

        TimingStatsHandler.log_measured_timing("JOB", self.name, self.start_time, current_run_time)

    @defer.inlineCallbacks
    def _operation(self):
        try:
            self.stats_collection_start()
        except:
            pass

        try:
            yield self.operation()
        except Exception as e:
            log.err("Exception while performing scheduled operation %s: %s" % \
                    (type(self).__name__, e))

            if isinstance(e, Failure):
                exc_type = [e.type, e.value, e.getTracebackObject()]
            else:
                exc_type, exc_value, exc_tb = sys.exc_info()

            mail_exception_handler(exc_type, exc_value, exc_tb)

        try:
            self.stats_collection_end()
        except:
            pass

    def operation(self):
        pass # dummy skel for GLJob objects
