# -*- encoding: utf-8 -*-

import time
import random

from twisted.internet.defer import inlineCallbacks
from twisted.internet import task
from globaleaks.tests import helpers
from globaleaks import anomaly
from globaleaks.handlers.statistics import get_stats, get_anomaly_history, delete_anomaly_history, delete_weekstats_history, AnomaliesCollection
from globaleaks.jobs.statistics_sched import StatisticsSchedule, AnomaliesSchedule, ResourceChecker, save_anomalies, save_statistics

anomaly.reactor = task.Clock()

class TestStatistics(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """
    supported_event = anomaly.Alarm.OUTCOME_ANOMALY_MAP.keys()

    @inlineCallbacks
    def test_save_anomalies(self):
        """
        How create anomalies: a lots of event + compute stress
        """

        # clean current queues
        anomaly.Alarm().compute_activity_level(notification=False)
        AnomaliesCollection.RecentAnomaliesQ = dict()

        # start test
        ANOMALIES_AMOUNT = 10
        anomaly.pollute_Event_for_testing(ANOMALIES_AMOUNT)
        anomaly.Alarm().compute_activity_level(notification=False)

        # but we got only one anomaly, because the computation make one
        # product for every thirty seconds

        # what matter is the content of the anomaly:
        # (Pdb) p AnomaliesCollection.RecentAnomaliesQ
        # {'2014-11-18T14:18:02':
        #       [{  'file': 80, 'receiver_message': 80,
        #           'wb_comment': 80, 'submission_completed': 80,
        #           'submission_started': 80, 'wb_message': 80,
        #           'login_success': 80, 'receiver_comment': 80,
        #           'login_failure': 80},
        #       2]}

        anomdet = AnomaliesCollection.RecentAnomaliesQ.values()[0]
        self.assertEqual(len(AnomaliesCollection.RecentAnomaliesQ.keys()), 1)
        original_when = AnomaliesCollection.RecentAnomaliesQ.keys()[0]

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




