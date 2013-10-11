# -*- coding: UTF-8
#   statistics_sched
#   ****************
#
#  Statistics works collecting every N-th minutes the amount of important
#  operations happened
import sys

from globaleaks.jobs.base import GLJob

class APSStatistics(GLJob):

    @staticmethod
    def operation():
        """
        Every node has two timeframe which the statistics are collected
        inside. All the operation happening during a timeframe
        are collected in the last row of PublicStats and AdminStats,
        this operation create a new row.
        """
        # just take AdminStats, initialize a new row
        # just take PublicStats, initialize a new row
        try:
            pass
        except:
            sys.excepthook(*sys.exc_info())

