# -*- coding: utf-8 -*-

# Implement anomalies check
from globaleaks.anomaly import check_anomalies
from globaleaks.jobs.base import LoopingJob


class Anomalies(LoopingJob):
    """
    This job checks for anomalies and take care of saving them on the db.
    """
    interval = 60

    def operation(self):
        check_anomalies()
