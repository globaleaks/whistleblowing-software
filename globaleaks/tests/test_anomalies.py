# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.jobs import statistics_sched
from globaleaks.settings import GLSetting, external_counted_events

class TestEmail(helpers.TestGL):

    def increment_accesses(self, amount):

        for element in external_counted_events.keys():
            GLSetting.anomalies_counter[element] = amount

    @inlineCallbacks
    def test_anomalies(self):
        yield helpers.TestGL.setUp(self)
        # First round 10
        self.increment_accesses(10)
        statistics_sched.AnomaliesSchedule().operation()
        # Second round 30
        self.increment_accesses(30)
        statistics_sched.AnomaliesSchedule().operation()
        # Third round 30
        self.increment_accesses(30)
        statistics_sched.AnomaliesSchedule().operation()
        # Stats!
        yield statistics_sched.StatisticsSchedule().operation()
