# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks
from twisted.internet import task

from globaleaks import anomaly
from globaleaks.handlers.admin.statistics import get_anomaly_history
from globaleaks.jobs.statistics_sched import StatisticsSchedule
from globaleaks.settings import GLSetting
from globaleaks.tests import helpers
from globaleaks.tests.test_anomaly import pollute_events_for_testing

anomaly.reactor = task.Clock()

class TestStatistics(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """
    supported_event = anomaly.Alarm.OUTCOMING_ANOMALY_MAP.keys()

    @inlineCallbacks
    def test_save_anomalies(self):
        """
        How create anomalies: a lots of event + compute stress
        """

        # start test
        ANOMALIES_AMOUNT = 50
        pollute_events_for_testing(ANOMALIES_AMOUNT)

        anomaly.compute_activity_level()

        anomdet = GLSetting.RecentAnomaliesQ.values()[0]
        self.assertEqual(len(GLSetting.RecentAnomaliesQ.keys()), 1)
        original_when = GLSetting.RecentAnomaliesQ.keys()[0]

        self.assertTrue(isinstance(anomdet, list))
        self.assertTrue(len(anomdet), 2)

        # alarm level was 2, right ?
        self.assertEqual(anomdet[1], 2, "Alarm raised is not 2 anymore ?")

        # every stuff need to be ANOMALIES_AMOUNT * 2, because
        # pollute function put two event each
        for event, amount in anomdet[0].iteritems():
            self.assertEqual(amount, ANOMALIES_AMOUNT * 2)

        # scheduler happen to save these anomalies, along with stats
        yield StatisticsSchedule().operation()

        # now if we get our anomalies, we expect the same 10, right ?
        AH = yield get_anomaly_history(limit=10)
        self.assertEqual(original_when, AH[0]['when'])
