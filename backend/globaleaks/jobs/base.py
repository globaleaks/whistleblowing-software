# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks
import exceptions
import time

from twisted.internet import task, defer, reactor
from twisted.python.failure import Failure

from globaleaks.handlers.base import TimingStatsHandler
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import send_exception_email,  extract_exception_traceback_and_send_email
from globaleaks.utils.utility import log


test_reactor = None


DEFAULT_JOB_MONITOR_TIME = 5 * 60 # seconds


class GLJob(object):
    name = "unnamed"
    job_runs = 0
    start_time = 0
    low_time = -1
    high_time = -1
    mean_time = -1

    monitor_time = DEFAULT_JOB_MONITOR_TIME

    def __init__(self):
        self.clock = reactor if test_reactor is None else test_reactor

        self.job = task.LoopingCall(self._operation)
        self.job.clock = self.clock

        self.monitor = task.LoopingCall(self.monitor_fun)
        self.monitor.clock = self.clock

    def monitor_fun(self):
        self.monitor_runs += 1
        elapsed_time = self.monitor_time * self.monitor_runs

        if elapsed_time < 60:
            error = "Job %s is taking more than %d seconds to execute" % (self.name, elapsed_time)
        elif elapsed_time < 3600:
            minutes = int(elapsed_time / 60)
            error = "Job %s is taking more than %d minutes to execute" % (self.name, minutes)
        else:
            hours = int(elapsed_time / 3600)
            error = "Job %s is taking more than %d hours to execute" % (self.name, hours)

        log.err(error)
        send_exception_email(error)

    def dead_fun(self, loopingCall):
        error = "Job %s is died with runtime %.4f [iterations: %d, low: %.4f, high: %.4f]" % \
                      (self.name, self.mean_time, self.job_runs, self.low_time, self.high_time)

        log.err(error)
        send_exception_email(error)

    def start_job(self, delay):
        d = self.job.start(delay)

        d.addErrback(self.dead_fun)

    def schedule(self, period = 1, delay = 0):
        delay = int(delay)

        if delay > 0:
            self.clock.callLater(delay, self.start_job, period)
        else:
            self.start_job(delay)

    def stats_collection_start(self):
        if self.mean_time != -1:
            log.time_debug("Starting job %s expecting an execution time of %.4f [iterations: %d low: %.4f, high: %.4f]" %
                           (self.name, self.mean_time, self.job_runs, self.low_time, self.high_time))
        else:
            log.time_debug("Starting job %s" % self.name)

        self.monitor_runs = 0
        self.start_time = time.time()
        self.job_runs += 1

        self.monitor.start(self.monitor_time, False)

    def stats_collection_end(self):
        if self.monitor.running:
            self.monitor.stop()

        current_run_time = time.time() - self.start_time

        # discard empty cicles from stats
        if current_run_time > 0.000000:
            self.mean_time = ((self.mean_time * (self.job_runs - 1)) + current_run_time) / (self.job_runs)

        if self.low_time == -1 or current_run_time < self.low_time:
            self.low_time = current_run_time

        if self.high_time == -1 or current_run_time > self.high_time:
            self.high_time = current_run_time

        log.time_debug("Job %s ended with an execution time of %.4f seconds" % (self.name, current_run_time))

        TimingStatsHandler.log_measured_timing("JOB", self.name, self.start_time, current_run_time)

    @defer.inlineCallbacks
    def _operation(self):
        self.stats_collection_start()

        try:
            yield self.operation()
        except Exception as e:
            log.err("Exception while performing scheduled operation %s: %s" % \
                    (type(self).__name__, e))

            extract_exception_traceback_and_send_email(e)

        self.stats_collection_end()
