# -*- coding: UTF-8
#   statistics_sched
#   ****************
#
#  Statistics works collecting every N-th minutes the amount of important
#  operations happened
import sys
from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601
from globaleaks.settings import GLSetting, transact, external_counted_events
from globaleaks.models import Stats


@transact
def acquire_statistics(store, anomalies_collection):
    newstat = Stats()
    newstat.content = dict(anomalies_collection)
    store.add(newstat)

# 'new_submission' : 0,
# 'finalized_submission': 0,
# 'anon_requests': 0,
# 'file_uploaded': 0,

# the level of the alarm in 30 seconds, to be moved in GLSetting
alarm_level = {
    'new_submission' : 20, # test
    'finalized_submission': 5,
    'anon_requests': 100, # this is just an amazing value, don't know if useful
    'file_uploaded': 10, # this is untrue, if someone select 30 little .doc, it's fine !?
}

alarm_template = {
    'new_submission' : "Has been reached 20 sumbmissions in 30 seconds",
    'finalized_submission': "Has been reached 5 finalized Tip in 30 seconds",
    'anon_requests': "Anonymous request more than 100 in 30 seconds",
    'file_uploaded': "10 files has been uploaded in the last 30 seconds"
}

class AnomaliesSchedule(GLJob):

    def operation(self):
        """
        Every X seconds is checked if anomalies are happening
        from anonymous interaction (submission/file/comments/whatever flood)

        two thing are done:
            1) checks if the threshold are under the 'danger level'
            2) copy them in the admin statistics memory table, this table is
                dumped in the database by scheduled ops StatisticsSchedule below
        """

        try:
            # print this log message only if something need to be reported
            if GLSetting.anomalies_counter['new_submission'] > 0 or \
               GLSetting.anomalies_counter['finalized_submission'] > 0 or \
               GLSetting.anomalies_counter['anon_requests'] > 0 or \
               GLSetting.anomalies_counter['file_uploaded'] > 0:

                log.debug("Anomalies checks [started submission %d, " \
                          "finalized submission %d, anon req %d, new files %d]" %
                          ( GLSetting.anomalies_counter['new_submission'],
                            GLSetting.anomalies_counter['finalized_submission'],
                            GLSetting.anomalies_counter['anon_requests'],
                            GLSetting.anomalies_counter['file_uploaded'] ) )

            # the newer on top of the older
            GLSetting.anomalies_list = [ GLSetting.anomalies_counter ] + GLSetting.anomalies_list

            # check the anomalies
            for element, alarm in alarm_level.iteritems():
                if GLSetting.anomalies_counter[element] > alarm:
                    GLSetting.anomalies_messages.append(
                        { 
                          'creation_date': datetime_to_ISO8601(datetime_now()),
                          'message': alarm_template[element]
                        })

            # clean the next collection dictionary
            GLSetting.anomalies_counter = dict(external_counted_events)

        except Exception as excep:
            log.err("Unable to collect the anomaly counters: %s" % excep)
            sys.excepthook(*sys.exc_info())


class StatisticsSchedule(GLJob):

    @inlineCallbacks
    def operation(self):

        try:
            stat_sum = dict(external_counted_events)
            for segment in GLSetting.anomalies_list:
                for key in external_counted_events.keys():
                    stat_sum[key] += segment[key]

            yield acquire_statistics(stat_sum)

        except Exception as excep:
            log.err("Unable to dump the anomalies in to the stats: %s" % excep)
            sys.excepthook(*sys.exc_info())

