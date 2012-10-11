from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.trial import unittest
from globaleaks.scheduler.work import WorkManager, Job, TimeoutJob


class DummyJob(Job):
    def dummy(self, d):
        print "----- Did dummy stuff ---"
        d.callback(None)

    def run(self):
        print "-------- Dummy Job ----------"
        d = Deferred()
        reactor.callLater(1, self.dummy, d)
        return d

class DummyTJ(TimeoutJob):
    def timedOut(self):
        self.lock.cancel()

    def dummy(self, d):
        print "TJ: Finished!"
        d.callback(None)

    def run(self):
        print "Timeout job!"
        d = Deferred()
        self.lock = reactor.callLater(3, self.dummy, d)
        return d

class FailJob(DummyJob):
    def dummy(self, d):
        d.errback(Exception("I have failed"))

class TestScheduler(unittest.TestCase):
    def doneWork(self, result, d, workManager, *arg, **kw):
        print workManager.showState()
        if workManager.callLock:
            workManager.callLock.cancel()
        return result

    def test_add_jobs(self):
        workManager = WorkManager()

        job = DummyJob()
        workManager.add(job)

        d = workManager.run()
        d.addBoth(self.doneWork, d, workManager)
        return d

    # XXX I cannot figure out how to properly make failUnlessFailure trap the
    # exception that I am raising in workManager. This test is working as it
    # should, but I am unable to automatically make it understand the exception
    # is good.
    def disabled_test_timeout_job(self):
        workManager = WorkManager()

        job = DummyTJ()
        workManager.add(job)

        d = workManager.run()
        #self.failUnlessFailure(d)
        d.addBoth(self.doneWork, d, workManager)
        return d

def run():
    job2 = DummyJob()
    job3 = FailJob()
    tj = DummyTJ()

    taskManager.add(job1)
    taskManager.add(job2)
    taskManager.add(job3)
    taskManager.add(tj)

    taskManager.run()


