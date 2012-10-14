
# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

import time
import datetime

from twisted.internet import reactor

class Job(object):
    def __init__(self, scheduledTime=time.time(), delay=None):
        self.scheduledTime = scheduledTime

        self.manager = None
        self.running = False
        self.failures = []
        if delay:
            self.scheduledTime += delay

    def __str__(self):
        return str("%s - %s - %s" % (self.__class__, self.scheduledTime, self.running))

    def schedule(self, date):
        if isinstance(date, datetime.datetime):
            self.scheduledTime = time.mktime(date.timetuple())
        else:
            raise Exception("date argument must be an instance of datetime")

    def _run(self, manager=None):
        d = self.run()
        self.manager = manager
        return d

    def run(self):
        pass

class JobTimedout(Exception):
    pass

class TimeoutJob(Job):
    timeout = 2
    def timedOut(self):
        pass

    def _timedOut(self, d, *arg, **kw):
        self.timedOut()
        d.errback(JobTimedout("%s timed out after %s" % (self.__class__,
            self.timeout)))

    def _run(self, manager=None):
        d = Job._run(self, manager)
        reactor.callLater(self.timeout, self._timedOut, d)
        return d

