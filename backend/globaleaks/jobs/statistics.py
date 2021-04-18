# -*- coding: utf-8 -*-
# Implement set of actions statistics actions executed on an hourly basis
from globaleaks.jobs.job import LoopingJob
from globaleaks.utils.utility import datetime_now

__all__ = ['Statistics']


class Statistics(LoopingJob):
    """
    Statistics
    """
    interval = 3600
    monitor_interval = 5 * 60

    def get_delay(self):
        current_time = datetime_now()
        return 3600 - (current_time.minute * 60) - current_time.second

    def operation(self):
        # Hourly Resets
        self.state.reset_hourly()

