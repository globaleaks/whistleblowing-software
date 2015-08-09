from twisted.internet import task

from globaleaks.utils.utility import log
from globaleaks.utils.mailutils import send_exception_email


DEFAULT_MONITOR_TIME = 5 * 60 # seconds


class ResourceMonitor(task.LoopingCall):
    run = 0

    def __init__(self, resource_name, monitor_time=DEFAULT_MONITOR_TIME):
        self.resource_name = resource_name
        self.monitor_time = monitor_time

        task.LoopingCall.__init__(self, self.tooMuch)
        self.start(self.monitor_time, False)

    def tooMuch(self):
        self.run += 1

        self.elapsed_time = self.monitor_time * self.run

        if (self.elapsed_time > 3600):
            hours = int(self.elapsed_time / 3600)
            error = "Warning: [%s] is taking more than %d hours to execute" % (self.resource_name, hours)
        if (self.elapsed_time > 60):
            minutes = int(self.elapsed_time / 60)
            error = "Warning: [%s] is taking more than %d minutes to execute" % (self.resource_name, minutes)
        else:
            error = "Warning: [%s] is taking more than %d seconds to execute" % (self.resource_name, self.elapsed_time)

        log.err(error)
        send_exception_email(error)
