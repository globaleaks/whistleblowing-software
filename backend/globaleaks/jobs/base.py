# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks

import sys
import time

from twisted.internet import task, defer
from twisted.python.failure import Failure

from globaleaks.utils.utility import log, deferred_sleep
from globaleaks.utils.mailutils import mail_exception_handler


class GLJob(task.LoopingCall):
    iterations = 0
    start_time = 0
    mean_time = 0
    name = "unnamed"

    def __init__(self):
        task.LoopingCall.__init__(self, self._operation)

    @defer.inlineCallbacks
    def _operation(self):
        try:
            self.start_time = int(time.time())

            if self.mean_time > 0:
                log.debug("Starting job [%s] expecting a mean execution time of %d" % (self.name, self.mean_time))
            else:
                log.debug("Starting job [%s]" % self.name)

            yield self.operation()

            current_run_time = int(time.time()) - self.start_time
            if current_run_time > 0:
                self.mean_time = int(((self.mean_time * self.iterations) + current_run_time) / (self.iterations + 1))

            log.debug("Ended job [%s] with an execution time of %d seconds" % (self.name, current_run_time))

            self.iterations += 1
        except Exception as e:
            log.err("Exception while performin scheduled operation %s: %s" % \
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
