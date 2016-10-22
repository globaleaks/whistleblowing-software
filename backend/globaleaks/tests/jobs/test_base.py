#nt -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, Deferred

from globaleaks.tests import helpers

from globaleaks.jobs.base import GLJob


class GLJobX(GLJob):
    period = 2
    operation_called = 0

    def operation(self):
        self.operation_called += 1


class TestGLJob(helpers.TestGL):
    @inlineCallbacks
    def test_base_scheduler(self):
        """
        This function asseses the functionalities of a scheduler in calling
        the operation() function periodically.
        """
        job = GLJobX()

        self.assertEqual(job.operation_called, 0)

        self.test_reactor.advance(1)

        self.assertEqual(job.operation_called, 1)

        self.test_reactor.advance(1)

        self.assertEqual(job.operation_called, 1)

        for i in range(2, 10):
            self.test_reactor.advance(2)
            self.assertEqual(job.operation_called, i)
