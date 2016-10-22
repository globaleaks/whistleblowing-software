# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks
import time
from twisted.internet import task, defer, reactor

from globaleaks.handlers.base import TimingStatsHandler
from globaleaks.utils.mailutils import send_exception_email,  extract_exception_traceback_and_send_email
from globaleaks.utils.utility import log


test_reactor = None


class GLJob(object):
    name = "unnamed"
    running = False
    period = 60
    low_time = -1
    high_time = -1
    mean_time = -1
    start_time = -1
    monitor_time = 5 * 60

    def __init__(self):
        self.clock = reactor if test_reactor is None else test_reactor

        self.job = task.LoopingCall(self._operation)
        self.job.clock = self.clock

        self._schedule()

    def _errback(self, loopingCall):
        error = "Job %s is died with runtime %.4f [low: %.4f, high: %.4f]" % \
                      (self.name, self.mean_time, self.low_time, self.high_time)

        log.err(error)
        send_exception_email(error)

    def start_job(self, period):
        self.job.start(period).addErrback(self._errback)

    def schedule(self):
        return 0

    def _schedule(self):
        delay = self.schedule()

        if delay < 1:
            delay = 1

        self.clock.callLater(delay, self.start_job, self.period)

    def stats_collection_begin(self):
        self.start_time = time.time()
        self.running = True

    def stats_collection_end(self):
        current_run_time = time.time() - self.start_time

        # discard empty cicles from stats
        if self.mean_time == -1:
            self.meantime = current_run_time
        else:
            self.mean_time = (self.mean_time * 0.7) + (current_run_time * 0.3)

        if self.low_time == -1 or current_run_time < self.low_time:
            self.low_time = current_run_time

        if self.high_time == -1 or current_run_time > self.high_time:
            self.high_time = current_run_time

        self.running = False

    @defer.inlineCallbacks
    def _operation(self):
        self.stats_collection_begin()

        try:
            yield self.operation()
        except Exception as e:
            log.err("Exception while performing scheduled operation %s: %s" % \
                    (type(self).__name__, e))

            extact_exception_traceback_and_send_email(e)

        self.stats_collection_end()


class GLJobsMonitor(GLJob):
    name = "jobs monitor"
    period = 2

    def __init__(self, jobs_list):
        GLJob.__init__(self)
        self.jobs_list = jobs_list

    #@defer.inlineCallbacks
    def operation(self):
        current_time = time.time()

        for job in self.jobs_list:
            execution_time = 0
            if job.running:
                execution_time = current_time - job.start_time

            if execution_time > job.monitor_time:
                if execution_time < 60:
                    error = "Job %s is taking more than %d seconds to execute" % (job.name, execution_time)
                elif execution_time < 3600:
                    minutes = int(execution_time / 60)
                    error = "Job %s is taking more than %d minutes to execute" % (job.name, minutes)
                else:
                    hours = int(execution_time / 3600)
                    error = "Job %s is taking more than %d hours to execute" % (job.name, hours)

                log.err(error)
                send_exception_email(error)
