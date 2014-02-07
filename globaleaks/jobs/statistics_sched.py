# -*- coding: UTF-8
#   statistics_sched
#   ****************
#
#  Statistics works collecting every N-th minutes the amount of important
#  operations happened
import sys

from globaleaks.jobs.base import GLJob
from globaleaks.utils.utility import log
from globaleaks.settings import GLSetting, external_counted_events

# Instead of a DB table we've a temporary area where store the statistics
temporary_dummy_db = []
# when globaleaks restart these data are lost

# 'new_submission' : 0,
# 'finalized_submission': 0,
# 'anon_requests': 0,
# 'file_uploaded': 0,



class APSStatistics(GLJob):

    @staticmethod
    def operation():
        """
        Every node has two timeframe which the statistics are collected
        inside. All the operation happening during a timeframe

        two thing are done:
            1) checks if the threshold are under the 'danger level'
            2) copy them in the admin statistics table
        """

        try:
            log.debug("Statistics loop collection [started submission %d, " \
                      "finalized submission %d, anon req %d, new files %d]" %
                      ( GLSetting.stats['new_submission'],
                        GLSetting.stats['finalized_submission'],
                        GLSetting.stats['anon_requests'],
                        GLSetting.stats['file_uploaded'] ) )


            temporary_dummy_db.append(GLSetting.stats)

            # clean the next collection dictionary
            GLSetting.stats = dict(external_counted_events)

        except:
            sys.excepthook(*sys.exc_info())
