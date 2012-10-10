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

    def run(self):
        pass

class DummyJob(Job):
    def dummy(self, d):
        print "----- Did dummy stuff ---"
        d.callback(None)

    def run(self):
        print "-------- Dummy Job ----------"
        d = Deferred()
        reactor.callLater(1, self.dummy, d)
        return d

class FailJob(DummyJob):
    def dummy(self, d):
        d.errback(Exception("I have failed"))


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
    retries = [3, 6, 10]

    def __init__(self):
        self.workQueue = []
        self.failedQueue = []

        self.runningJobs = []

        self.nextRun = time.time()
        self.callLock = False

    def add(self, obj):
        """
        Adds an object to the queue. The object must have the attribute .run()
        set to something that will return a deferred.
        """
        print "Adding %s to queue" % obj
        if obj.running:
            print "It appears that %s is still running" % obj
        obj.running = False

        self.workQueue.append(obj)

        print "[!] This job is to be run before the already scheduled next run"
        self.nextRun = obj.scheduledTime

        if not self.callLock:
            print "The call lock is not set, therefore we will register to call later"
            reactor.callLater(self.getTimeout(), self.run)
            self.callLock = True

        print "Going to run in %s" % self.getTimeout()

    def _success(self, result, obj):
        print "[*] Completed task %s" % obj
        self.workQueue.remove(obj)
        obj.running = False

    def _completed(self, result, obj):
        print "[*] did all my calls."

    def _failed(self, failure, obj):
        print "[!] Failed on %s" % obj
        obj.failures.append(failure)
        self.workQueue.remove(obj)
        if len(obj.failures) > len(self.retries):
            # Too many failures, give up trying
            print "[!] Giving up on this one."
            self.failedQueue.append(obj)
        else:
            print "[*] Re-adding to the queue"
            obj.scheduledTime = time.time()
            obj.scheduledTime += self.retries[len(obj.failures) - 1]
            obj.running = False
            self.add(obj)
        return failure

    def showState(self):
        print "Fail Queue"
        for x in self.workQueue:
            print x
        print "Work Queue"
        for x in self.failedQueue:
            print x

    def saveState(self, output='manager.state'):
        print "Saving state"
        fp = open(output, 'w')
        pickle.dump(self, fp)
        fp.close()

    def _done(self, result):
        self.saveState()


    def run(self):
        print "[*] Running!"
        dlist = []
        current_time = time.time()
        run_later = False

        self.saveState()
        self.callLock = False

        for obj in self.workQueue:
            print "[*] Processing this obj: %s" % obj

            if current_time < obj.scheduledTime:
                print "[!] We are not ready to run this object"
                if obj.scheduledTime < self.nextRun:
                    print "[!] Setting the next clock to hit on this object"
                    self.nextRun = obj.scheduledTime
                run_later = True
                continue

            if not obj.running:
                print "Running %s" % obj
                obj.running = True
                d = obj.run()
                d.addErrback(self._failed, obj)
                d.addCallback(self._success, obj)
                dlist.append(d)
            else:
                print "Object already running!"

        print "Next call %s - %s" % (self.nextRun, current_time)
        print "dl %s" % dlist

        if run_later:
            print "We should run again!"
            reactor.callLater(self.getTimeout(), self.run)
            self.callLock = True

        dl = DeferredList(dlist)
        dl.addBoth(self._done)
        self.runningJobs = dl
        return dl

    def getTimeout(self):
        timeout = int(self.nextRun - time.time()) + 1
        if timeout < 0:
            print "[!] Got a negative timeout"
            timeout = 1
        return timeout

try:
    taskManager = pickle.load(open('manager.state', 'r'))
    print taskManager.showState()

except:
    print "No state file, creating a new instance!"
    taskManager = WorkManager()

job1 = DummyJob()
job2 = DummyJob()
job3 = FailJob()

taskManager.add(job1)
taskManager.add(job2)
taskManager.add(job3)

taskManager.run()

reactor.run()


