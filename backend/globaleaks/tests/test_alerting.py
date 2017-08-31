# -*- encoding: utf-8 -*-
from globaleaks.anomaly import Alarm
from globaleaks.handlers.admin.statistics import get_anomaly_history
from globaleaks.jobs.statistics_sched import StatisticsSchedule
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_to_ISO8601
from twisted.internet.defer import inlineCallbacks


class TestStatistics(helpers.TestGL):
    """
    This test mostly the function in anomaly.py Alarm object
    """

    @inlineCallbacks
    def test_save_anomalies(self):
        """
        How create anomalies: a lots of event + compute stress
        """

        # start test
        ANOMALIES_COUNT = 50
        self.pollute_events(ANOMALIES_COUNT)

        Alarm.compute_activity_level()

        anomdet = GLSettings.RecentAnomaliesQ.values()[0]
        self.assertEqual(len(GLSettings.RecentAnomaliesQ.keys()), 1)
        original_date = datetime_to_ISO8601(GLSettings.RecentAnomaliesQ.keys()[0])

        self.assertTrue(isinstance(anomdet, list))
        self.assertTrue(len(anomdet), 2)

        # alarm level was 2, right ?
        self.assertEqual(anomdet[1], 2, "Alarm raised is not 2 anymore ?")

        # every stuff need to be ANOMALIES_AMOUNT * 2, because
        # pollute function put two event each
        for event, count in anomdet[0].items():
            self.assertEqual(count, ANOMALIES_COUNT * 2)

        # scheduler happen to save these anomalies, along with stats
        yield StatisticsSchedule().run()

        # now if we get our anomalies, we expect the same 10, right ?
        AH = yield get_anomaly_history(limit=10)
        self.assertEqual(original_date, AH[0]['date'])
