# -*- coding: UTF-8
#   statistics_sched
#   ****************
#
#  Statistics works collecting every N-th minutes the amount of important
#  operations happened
import sys
from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.utils.utility import log
from globaleaks.settings import GLSetting, transact, external_counted_events
from globaleaks.models import Stats


def serialize_events(collected):

    retdict = {}
    for key in external_counted_events.keys():
        retdict.update({key: collected[key]})
        print "serialized: %s : %s" % (key, collected[key])

    return retdict

@transact
def acquire_statistics(store, anomalies_collection):

    log.debug("Acquiring anomalies in stats")
    log.debug("%s" % serialize_events(anomalies_collection))
    newstat = Stats()
    newstat.content = dict(anomalies_collection)
    store.add(newstat)


# 'new_submission' : 0,
# 'finalized_submission': 0,
# 'anon_requests': 0,
# 'file_uploaded': 0,

class APSAnomalies(GLJob):

    @staticmethod
    def operation():
        """
        Every X seconds is checked if anomalies are happening
        from anonymous interaction (submission/file/comments/whatever flood)

        two thing are done:
            1) checks if the threshold are under the 'danger level'
            2) copy them in the admin statistics memory table, this table is
                dumped in the database by scheduled ops APSStatistics below
        """

        try:
            log.debug("Anomalies loop collection [started submission %d, " \
                      "finalized submission %d, anon req %d, new files %d]" %
                      ( GLSetting.anomalies_counter['new_submission'],
                        GLSetting.anomalies_counter['finalized_submission'],
                        GLSetting.anomalies_counter['anon_requests'],
                        GLSetting.anomalies_counter['file_uploaded'] ) )

            GLSetting.anomalies_list.append(GLSetting.anomalies_counter)
            log.debug("%s" % serialize_events(GLSetting.anomalies_counter))

            # clean the next collection dictionary
            GLSetting.anomalies_counter = dict(external_counted_events)

        except Exception as excep:
            log.err("Unable to collect the anomaly counters: %s" % excep)
            sys.excepthook(*sys.exc_info())


class APSStatistics(GLJob):

    @staticmethod
    @inlineCallbacks
    def operation():

        try:
            stat_sum = dict(external_counted_events)
            for segment in GLSetting.anomalies_list:
                for key in external_counted_events.keys():
                    stat_sum[key] += segment[key]

            log.debug("Statistic ready to be acquired!")
            log.debug("%s" % serialize_events(stat_sum))

            yield acquire_statistics(stat_sum)

        except Exception as excep:
            log.err("Unable to dump the anomalies in to the stats: %s" % excep)
            sys.excepthook(*sys.exc_info())

