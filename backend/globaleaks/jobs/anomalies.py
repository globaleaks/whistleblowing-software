# -*- coding: utf-8 -*-

# Implement anomalies check
from twisted.internet.defer import inlineCallbacks

from globaleaks.anomaly import check_anomalies
from globaleaks.jobs.base import LoopingJob


class Anomalies(LoopingJob):
    """
    This job checks for anomalies and take care of saving them on the db.
    """
    interval = 60

    @inlineCallbacks
    def operation(self):
        yield check_anomalies()
