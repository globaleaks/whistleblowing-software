# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks

import sys
import time

from twisted.internet import task, defer, reactor
from twisted.python.failure import Failure

from globaleaks.utils.mailutils import mail_exception_handler
from globaleaks.utils.monitor import ResourceMonitor
from globaleaks.utils.utility import log


JOB_MONITOR_TIME = 5 * 60 # seconds


class GLJob(task.LoopingCall):
    iterations = 0
    start_time = 0
    mean_time = -1
    low_time = -1
    high_time = -1
    name = "unnamed"

    monitor = None

    def __init__(self):
        task.LoopingCall.__init__(self, self._operation)

    def stats_collection_start(self):
        self.monitor = ResourceMonitor(("[Job %s]" % self.name), JOB_MONITOR_TIME)

        self.start_time = time.time()

        if self.mean_time != -1:
            log.time_debug("Starting job [%s] expecting an execution time of %.2f [low: %.2f, high: %.2f]" %
                      (self.name, self.mean_time, self.low_time, self.high_time))
        else:
            log.time_debug("Starting job [%s]" % self.name)

    def stats_collection_end(self):
        if self.monitor is not None:
            self.monitor.stop()
            self.monitor = None

        current_run_time = time.time() - self.start_time

        # discard empty cicles from stats
        if current_run_time > 0.00:
            self.mean_time = ((self.mean_time * self.iterations) + current_run_time) / (self.iterations + 1)

        if self.low_time == -1 or current_run_time < self.low_time:
            self.low_time = current_run_time

        if self.high_time == -1 or current_run_time > self.high_time:
            self.high_time = current_run_time

        log.time_debug("Ended job [%s] with an execution time of %.2f seconds" % (self.name, current_run_time))

        self.iterations += 1

        if self.name == 'Delivery':
            from globaleaks.handlers.exporter import add_measured_event
            add_measured_event(None, None, current_run_time, self.iterations)

    @defer.inlineCallbacks
    def _operation(self):
        try:
            self.stats_collection_start()

            yield self.operation()

            self.stats_collection_end()
        except Exception as e:
            log.err("Exception while performing scheduled operation %s: %s" % \
                    (type(self).__name__, e))

            try:
                if isinstance(e, Failure):
                    exc_type = e.type
                    exc_value = e.value
                    exc_tb = e.getTracebackObject()
                else:
                    exc_type, exc_value, exc_tb = sys.exc_info()

                mail_exception_handler(exc_type, exc_value, exc_tb)
            except Exception:
                pass

    def operation(self):
        pass # dummy skel for GLJob objects
