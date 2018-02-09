# -*- coding: utf-8 -*-
from globaleaks import anomaly
from globaleaks.jobs import anomalies
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestAnomalies(helpers.TestGL):
    @inlineCallbacks
    def test_anomalies(self):
        self.n = 0

        full_ammo = 1000000

        original_get_disk_anomaly_conditions = anomaly.get_disk_anomaly_conditions

        conditions_count = len(original_get_disk_anomaly_conditions(full_ammo, full_ammo))

        def mock_get_disk_anomaly_conditions(*args, **kwargs):
            conditions = original_get_disk_anomaly_conditions(*args, **kwargs)
            # activate one condition at once
            for condition in enumerate(conditions):
                conditions[condition[0]]['condition'] = (condition[0] == self.n)

            return conditions

        anomaly.get_disk_anomaly_conditions = mock_get_disk_anomaly_conditions

        # testing the scheduler with all the conditions unmet
        self.n = -1
        yield anomalies.Anomalies().run()

        # testing the scheduler enabling all conditions one at once
        for j in range(conditions_count):
            self.n = j
            yield anomalies.Anomalies().run()

        yield anomalies.Anomalies().run()

        # testing the scheduler with all the conditions unmet
        # a second time in order test the accept_submissions value
        self.n = -1
        yield anomalies.Anomalies().run()
