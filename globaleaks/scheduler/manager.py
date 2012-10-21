# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

import time

from twisted.internet import reactor
from twisted.internet.defer import DeferredList, Deferred

from twisted.internet.threads import deferToThreadPool

from globaleaks import scheduler_threadpool
from globaleaks.utils import log, gltime

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

    WARNING API CHANGE:
    the retries parameter is now part of Job.
    """
    def __init__(self):
        self.workQueue = []
        self.failedQueue = []
        self.timeoutQueue = []

        self.runningJobs = []

        self.nextRun = time.time()

        self.callLock = None
        self.nextCall = time.time()

        self.deferred = Deferred()

    def add(self, obj, *arg):
        """
        Adds a Job object to the queue. args specifies the arguments to be
        passed to run when running the job.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "add", "obj", obj)
        obj.running = False
        obj.arg = arg

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

    def run(self):
        """
        Here we actually go through the work that is the queue.
        We then return a deferred list that contains the jobs that are now
        currently running.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "run")
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
                # XXX figure out how to do the multithreaded version of this
                d = deferToThreadPool(reactor, scheduler_threadpool,
                        obj._run, self)
                d.addErrback(self._failed, obj)
                d.addCallback(self._success, obj)
                dlist.append(d)
                #obj._run(self)

        if run_later:
            # We should set the schedule clock to hit again because there are
            # items that are not ready to be run just yet.
            self.callLock = reactor.callLater(self.getTimeout(), self.run)

        dl = DeferredList(dlist)
        dl.addBoth(self._done)
        self.runningJobs = dl



    def _success(self, result, obj):
        """
        We have successfully run the Job obj.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "_success", "result", result, "obj", obj)
        obj.success()
        self.workQueue.remove(obj)
        obj.running = False

    def _failed(self, failure, obj):
        """
        This Job obj has failed. We should figure out if it's worth our time to
        try again.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "_failed", "failure", failure, "obj", obj)
        log.debug("The job %s has failed" % obj)
        obj.failures.append(failure)
        self.workQueue.remove(obj)

        if len(obj.failures) > len(obj.retries):
            log.debug("Too many failures, give up trying")
            obj.failedRetries()
            self.failedQueue.append(obj)
        else:
            log.debug("Rescheduling the event")
            obj.failed()
            obj.scheduledTime = time.time()
            obj.scheduledTime += obj.retries[len(obj.failures) - 1]
            obj.running = False
            log.debug("Going to run it at %s" % gltime.timeToPrettyDate(obj.scheduledTime))
            self.add(obj)
        return failure

    def showState(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "showState")
        log.debug("Work Queue")
        for x in self.workQueue:
            log.debug("* "+x)
        log.debug("Failed Queue")
        for x in self.failedQueue:
            log.debug("* "+x)

    def loadState(self):
        """
        Put in here your logic for resting state.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "loadState")
        log.debug("loading state.")
        pass

    def saveState(self, output='manager.state'):
        """
        This saves the current state to a local pickle file.
        XXX replace this to write the state to database.
        """
        #fp = open(output, 'w+')
        #pickle.dump(self, fp)
        #fp.close()
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "saveState", "output", output)
        pass

    def _done(self, result, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "_done", "result", result)
        log.debug("Run all jobs in the deferred list. Saving state.")
        self.saveState()
        log.debug("State saved")
        if len(self.workQueue) == 0:
            log.debug("The work queue is empty. I am going to start idling.")
            self.deferred.callback(None)

    def getTimeout(self):
        """
        Returns the distance in seconds from when the next run of the schedule
        clocks should happen. We add a 1 as margin to round to the upper
        nearest whole number (we just don't want to be off by half a second
        when we hit run again).
        If the distance is negative we set the timeout to 1.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class WorkManager", "getTimeout")
        timeout = int(self.nextRun - time.time()) + 1
        if timeout < 0:
            timeout = 1
        return timeout

class DBWorkManager(WorkManager):
    """
    This is a database driven work manager. It uses the provided database to
    store the current state of the work queues.
    """

    log.debug("[D] %s %s " % (__file__, __name__), "Class DBWorkManager")

    def saveState(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class DBWorkManager", "saveState")
        print "Saving state to DB"

    def restoreState(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class DBWorkManager", "restoreState")
        print "Restoring state from DB"


work_manager = DBWorkManager()
work_manager.restoreState()

