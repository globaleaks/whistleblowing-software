# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

import time
import datetime
import pickle

from twisted.internet import reactor
from twisted.internet.defer import DeferredList, Deferred

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

class WorkManager(object):
    """
    WorkManager is a queue driven job scheduler. You can add jobs to it
    and it will schedule them for execution.
    It handles errors by scheduling retries at a series of specified
    intervals.

    Every time it starts going through the job queue it writes it's state. When
    it has finished iterating over the jobs and starting them it will write the
    state again.

    This allows it to resume state across restarts.

    retries: through this parameter you can specify a list of intervals after
    which a retry should happen. This is time in seconds.
    XXX in the future we may want to support a cronish like syntax for such
        timeouts (1m, 1h, 2d, 1m etc.)
    """
    retries = [1]

    def __init__(self):
        self.workQueue = []
        self.failedQueue = []
        self.timeoutQueue = []

        self.runningJobs = []

        self.nextRun = time.time()

        self.callLock = None
        self.nextCall = time.time()

        self.deferred = Deferred()

    def add(self, obj):
        """
        Adds an object to the queue. The object must have the attribute .run()
        set to something that will return a deferred.
        """
        obj.running = False

        self.workQueue.append(obj)

        # Set the next time to run to this newly added object we will set the
        # next time to hit the scheduler to the most optimal value when we do
        # the next run.
        # For the time being we are either about to hit the scheduler again

        if self.callLock and obj.scheduledTime < self.nextRun:
            self.nextRun = obj.scheduledTime
            self.callLock.cancel()

        if not self.callLock:
            # The call lock is not set, therefore we will register to call later
            self.nextRun = obj.scheduledTime
            self.callLock = reactor.callLater(self.getTimeout(), self.run)


    def _success(self, result, obj):
        # Successfully completed the job
        self.workQueue.remove(obj)
        obj.running = False

    def _failed(self, failure, obj):
        obj.failures.append(failure)
        self.workQueue.remove(obj)

        if len(obj.failures) > len(self.retries):
            # Too many failures, give up trying
            self.failedQueue.append(obj)
        else:
            # Reschedule the envent by readding it to the queue
            obj.scheduledTime = time.time()
            obj.scheduledTime += self.retries[len(obj.failures) - 1]
            obj.running = False
            self.add(obj)
        return failure

    def showState(self):
        print "Work Queue"
        print "----------"
        for x in self.workQueue:
            print x
        print "----------"
        print ""
        print "Failed Queue"
        print "----------"
        for x in self.failedQueue:
            print x
        print "----------"

    def saveState(self, output='manager.state'):
        """
        This saves the current state to a local pickle file.
        XXX replace this to write the state to database.
        """
        #fp = open(output, 'w+')
        #pickle.dump(self, fp)
        #fp.close()
        pass

    def _done(self, result, *arg, **kw):
        self.saveState()
        if len(self.workQueue) == 0:
            self.deferred.callback(None)

    def run(self):
        """
        Here we actually go through the work that is the queue.
        We then return a deferred list that contains the jobs that are now
        currently running.
        """
        dlist = []
        current_time = time.time()
        run_later = False

        self.saveState()
        self.callLock = None

        for obj in self.workQueue:
            if current_time < obj.scheduledTime:
                # We are not ready to run this object
                if obj.scheduledTime < self.nextRun:
                    # Setting the next clock to hit on this object
                    self.nextRun = obj.scheduledTime
                run_later = True
                continue

            if not obj.running:
                obj.running = True
                d = obj._run(self)
                d.addErrback(self._failed, obj)
                d.addCallback(self._success, obj)
                dlist.append(d)

        if run_later:
            # We should set the schedule clock to hit again because there are
            # items that are not ready to be run just yet.
            self.callLock = reactor.callLater(self.getTimeout(), self.run)

        dl = DeferredList(dlist)
        dl.addBoth(self._done)
        self.runningJobs = dl

        return self.deferred

    def getTimeout(self):
        """
        Returns the distance in seconds from when the next run of the schedule
        clocks should happen. We add a 1 as margin to round to the upper
        nearest whole number (we just don't want to be off by half a second
        when we hit run again).
        If the distance is negative we set the timeout to 1.
        """
        timeout = int(self.nextRun - time.time()) + 1
        if timeout < 0:
            timeout = 1
        return timeout


