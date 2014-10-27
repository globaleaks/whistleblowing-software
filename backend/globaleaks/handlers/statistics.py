# -*- coding: UTF-8
#
#   statistics
#   **********
#
# Implementation of classes handling the HTTP request to /node, public
# exposed API.

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.settings import transact_ro, GLSetting, external_counted_events
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.models import Stats
from globaleaks.utils.utility import datetime_to_ISO8601

@transact_ro
def admin_serialize_stats(store, language=GLSetting.memory_copy.default_language):

    stats = store.find(Stats)
    stats.order_by(Desc(Stats.creation_date))

    full_stats = []
    limit  =0
    for stat in stats:

        limit += 1
        if limit >= GLSetting.anomalies_report_limit:
            break

        single_stat = { 'creation_date' : datetime_to_ISO8601(stat.creation_date) }

        for element in external_counted_events.keys():
            single_stat.update({element : stat.content[element] })

        full_stats.append(single_stat)

    return full_stats


class AnomaliesCollection(BaseHandler):
    """
    This Handler returns the list of the triggered anomalies based on
    activity monitored in a timedelta (is considered anomalous if they
    reach the thresholds defined in GLSettings)
    """

    @transport_security_check("admin")
    @authenticated("admin")
    def get(self, *uriargs):

        # are kept the last 'GLSetting.anomalies_report_limit' number of informative element
        # because they are kept in memory. they are not lost, but summed in the statistics
        if len(GLSetting.anomalies_messages) > GLSetting.anomalies_report_limit:
            GLSetting.anomalies_messages = GLSetting.anomalies_messages[:GLSetting.anomalies_report_limit]

        self.finish(GLSetting.anomalies_messages)


class StatsCollection(BaseHandler):
    """
    This Handler returns the list of the stats, stats is the aggregated amount of
    activities recorded in the delta defined in GLSettings
    """

    @transport_security_check("admin")
    @authenticated("admin")
    @inlineCallbacks
    def get(self, *uriargs):

        stats_block = yield admin_serialize_stats()
        self.finish(stats_block)



