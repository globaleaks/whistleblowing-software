# -*- coding: UTF-8
#   statistics_sched
#   ****************
# 
#  Statistics works collecting every N-th minutes the amount of important 
#  operations happened


from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from datetime import datetime

__all__ = ['APSStatistics' ]


class APSStatistics(GLJob):

    def operation(self):
        """
        Every node has two timeframe which the statistics are collected 
        inside. All the operation happening during a timeframe
        are collected in the last row of PublicStats and AdminStats,
        this operation create a new row.
        """
        pass
        # just take AdminStats, initialize a new row
        # just take PublicStats, initialize a new row
