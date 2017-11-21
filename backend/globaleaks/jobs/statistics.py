# -*- coding: utf-8 -*-
# Implement collection of statistics

from globaleaks.jobs.base import LoopingJob
from globaleaks.models import Stats
from globaleaks.orm import transact_sync
from globaleaks.utils.utility import datetime_now, log


def get_statistics(state):
    stats = {}

    for tid in state.tenant_state:
        stats[tid] = {}
        for e in state.tenant_state[tid].EventQ:
            stats[tid].setdefault(e.event_type, 0)
            stats[tid][e.event_type] += 1

    return stats


@transact_sync
def save_statistics(store, start, end, stats):
    for tid in stats:
        newstat = Stats()
        newstat.tid = tid
        newstat.start = start
        newstat.summary = stats[tid]
        store.add(newstat)


class Statistics(LoopingJob):
    """
    Statistics collection scheduler run hourly
    """
    interval = 3600
    monitor_interval = 5 * 60

    def get_start_time(self):
        current_time = datetime_now()
        return 3600 - (current_time.minute * 60) - current_time.second

    def __init__(self):
        self.stats_collection_start_time = datetime_now()
        LoopingJob.__init__(self)

    def operation(self):
        current_time = datetime_now()
        statistic_summary = get_statistics(self.state)
        if statistic_summary:
            save_statistics(self.state.stats_collection_start_time, current_time, statistic_summary)
            log.debug("Stored statistics %s collected from %s to %s",
                      statistic_summary,
                      self.state.stats_collection_start_time,
                      current_time)

        # Hourly Resets
        self.state.reset_hourly()
