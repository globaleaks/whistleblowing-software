# -*- coding: UTF-8
#   task
#   ****
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Contains all the logic for handling tip related operations.

from zope.interface import Interface, Attribute
from twisted.internet import defer
from twisted.internet import reactor

import itertools

class TaskQueue(object):
    def __init__(self, maxconcurrent=10, subTask=None):
        self.maxconcurrent = maxconcurrent
        self._running = 0
        self._queued = []

    def _run(self, r):
        self._running -= 1
        if self._running < self.maxconcurrent and self._queued:
            workunit, d = self._queued.pop(0)
            self._running += 1
            actuald = workunit.startTask().addBoth(self._run)
        if isinstance(r, failure.Failure):
            r.trap()

        print "Callback fired!"
        print r['start_time']
        print r['end_time']
        print r['run_time']
        print repr(r)
        return r

    def push(self, workunit):
        if self._running < self.maxconcurrent:
            self._running += 1
            workunit.startTask().addBoth(self._run)
            return
        d = defer.Deferred()
        self._queued.append((workunit, d))
        return d


class DummyMethod:
    def __init__(self, type):
        self.type = type
        # remind: wtf ?
        self.deferred = defer.Deferred()

    def deliver(self, receiver):
        print "Doing delivery via %s" % self.type
        print "To: %s" % receiver

    def notify(self, receiver):
        print "Doing notification via %s" % self.type
        print "To: %s" % receiver

    def periodic_24H(self, stuff):
        print "Every 24 hours this task must run, but I don't get the DummyMethod concept"
        print "stuff", stuff

class Task:
    """
    Object responsible for handling the creation of delivery and notification
    task to receivers.
    """
    receiver = None
    type = None
    tip = None

    def __init__(self, type, receiver, tip):
        print "Task", type, receiver, tip
        self.type = type
        self.receiver = receiver
        self.notify_method = self._get_notification_method()
        self.delivery_method = self._get_delivery_method()
        self.tip = tip
        #self.deferred.addCallbacks(self.callback, self.errback)

    def _get_delivery_method(self):
        return DummyMethod(self.type)

    def _get_notification_method(self):
        return DummyMethod(self.type)

    """
    Task contains periodic activity like:
    24H cleaning of unfinished session
    1M don't know, just for test
    periodic event: required for output accumulation, like multiple notification
    """
    def _get_periodic_24H(self):
        return DummyMethod(self.type)

    def _get_periodic_1M(self):
        return DummyMethod(self.type)

    def _get_periodic_flush(self):
        return DummyMethod(self.type)

    def spam_check(self):
        # why spam check goes here and not in the InputFilter hook ?
        pass

    def doneTask(self):
        self.delivery_method.deliver(self.receiver)
        self.notify_method.notify(self.receiver)
        return self.d.callback(str(self.receiver))

    def startTask(self):
        self.d = defer.Deferred()
        print "Starting task %s" % (self.receiver)
        reactor.callLater(1, self.doneTask)
        return self.d

def success(aa):
    print "DOne!"

def failed(bbb):
    print "Failed"

taskList = [Task('email', 'art'+str(x)+'@fuffa.org', {'a':1, 'b':2}) for x in range(0, 20)]
taskpool = TaskQueue(4)

for task in taskList:
    print "aaaa"
    taskpool.push(task)

reactor.run()
