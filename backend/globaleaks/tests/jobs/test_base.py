#nt -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, Deferred

from globaleaks.tests import helpers

from globaleaks.jobs.base import GLJob

class TestGLJob(helpers.TestGL):
    @inlineCallbacks
    def test_base_scheduler_1(self):
        """
        This function asseses the functionalities of a scheduler in calling
        the operation() function periodically.
        """
        class GLJobX(GLJob):
            monitor_time = 1000000
            operation_called = 0
            monitor_called = 0

            def operation(self):
                self.operation_called += 1

            def monitor_fun(self):
                self.monitor_called += 1

        job = GLJobX()
        yield job.schedule(1000, 3)

        self.assertEqual(job.operation_called, 0)
        self.assertEqual(job.monitor_called, 0)

        self.test_reactor.advance(3)

        self.assertEqual(job.operation_called, 1)
        self.assertEqual(job.monitor_called, 0)

        for i in range(2, 10):
            self.test_reactor.advance(1000)
            self.assertEqual(job.operation_called, i)
            self.assertEqual(job.monitor_called, 0)

    @inlineCallbacks
    def test_base_scheduler_2(self):
        """
        This function asseses the functionalities of a scheduler in calling
        the monitor_fun() function periodically in order to monitor the job.
        """
        class GLJobX(GLJob):
            monitor_time = 1000
            operation_called = 0
            monitor_called = 0

            @inlineCallbacks
            def operation(self):
                self.operation_called += 1

                # to sleep is like to die
                yield Deferred()

            def monitor_fun(self):
                self.monitor_called += 1

        job = GLJobX()
        yield job.schedule(1000000, 3)

        self.assertEqual(job.operation_called, 0)
        self.assertEqual(job.monitor_called, 0)

        self.test_reactor.advance(3)

        self.assertEqual(job.operation_called, 1)
        self.assertEqual(job.monitor_called, 0)

        self.test_reactor.advance(999)

        self.assertEqual(job.operation_called, 1)
        self.assertEqual(job.monitor_called, 0)

        self.test_reactor.advance(1)

        self.assertEqual(job.operation_called, 1)
        self.assertEqual(job.monitor_called, 1)

        for i in range(2, 10):
            self.test_reactor.advance(1000)
            self.assertEqual(job.operation_called, 1)
            self.assertEqual(job.monitor_called, i)
