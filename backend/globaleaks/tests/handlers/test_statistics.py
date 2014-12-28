# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from twisted.internet import task

from globaleaks.tests import helpers
from globaleaks.handlers import statistics
from globaleaks.jobs.statistics_sched import AnomaliesSchedule, StatisticsSchedule
from globaleaks import anomaly
from globaleaks.utils.utility import datetime_now

anomaly.reactor = task.Clock()
StatisticsSchedule.collection_start_datetime = datetime_now()

class TestStatsCollection(helpers.TestHandler):
    _handler = statistics.StatsCollection

    @inlineCallbacks
    def test_get(self):

        handler = self.request({}, role='admin')
        yield handler.get(0)
        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 7 * 24)

        anomaly.pollute_Event_for_testing(5)

        yield AnomaliesSchedule().operation()

        handler = self.request({}, role='admin')
        yield handler.get(0)

        self.assertEqual(len(self.responses), 2)
        self.assertEqual(len(self.responses[1]), 7 * 24)


class TestAnomHistCollection(helpers.TestHandler):
    _handler = statistics.AnomalyHistoryCollection

    @inlineCallbacks
    def test_get(self):

        anomaly.pollute_Event_for_testing(10)
        yield AnomaliesSchedule().operation()

        yield StatisticsSchedule().operation()
        handler = self.request({}, role='admin')
        yield handler.get()
        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)


