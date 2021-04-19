# -*- coding: utf-8
# Implement storage of audit log
from twisted.internet.defer import inlineCallbacks

from globaleaks.models import AuditLog
from globaleaks.orm import transact
from globaleaks.jobs.job import LoopingJob
from globaleaks.state import State

__all__ = ['AuditLogJob']


@transact
def log(session):
    while State.TempLogs:
        session.add(State.TempLogs.pop(0))


class AuditLogJob(LoopingJob):
    interval = 30

    @inlineCallbacks
    def operation(self):
        yield log()

    @inlineCallbacks
    def stop(self):
        yield self.operation()
        yield LoopingJob.stop(self)
