# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from twisted.internet import task

from globaleaks import anomaly
from globaleaks.handlers import statistics
from globaleaks.jobs.statistics_sched import AnomaliesSchedule, StatisticsSchedule
from globaleaks.models import Stats
from globaleaks.settings import transact_ro
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_now

anomaly.reactor = task.Clock()
StatisticsSchedule.collection_start_datetime = datetime_now()

class TestAnomaliesCollection(helpers.TestHandler):
    _handler = statistics.AnomaliesCollection

    @inlineCallbacks
    def test_get(self):
        anomaly.pollute_Event_for_testing(3)
        yield AnomaliesSchedule().operation()

        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertTrue(isinstance(self.responses[0], dict))

class TestStatsCollection(helpers.TestHandler):
    _handler = statistics.StatsCollection

    @transact_ro
    def get_stats_count(self, store):
        return store.find(Stats).count()

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get(0)

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 7 * 24)

        anomaly.pollute_Event_for_testing(3)

        yield AnomaliesSchedule().operation()

        handler = self.request({}, role='admin')
        yield handler.get(0)

        self.assertEqual(len(self.responses), 2)
        self.assertEqual(len(self.responses[1]), 7 * 24)

    @inlineCallbacks
    def test_delete(self):
        anomaly.pollute_Event_for_testing(3)
        yield AnomaliesSchedule().operation()
        yield StatisticsSchedule().operation()

        # be sure that Stats is populated
        count = yield self.get_stats_count()
        self.assertEqual(count, 1)

        # delete stats
        handler = self.request({}, role='admin')
        yield handler.delete()

        # verify that stats are now empty
        count = yield self.get_stats_count()
        self.assertEqual(count, 0)


class TestAnomHistCollection(helpers.TestHandler):
    _handler = statistics.AnomalyHistoryCollection

    @inlineCallbacks
    def test_get(self):
        anomaly.pollute_Event_for_testing(3)
        yield AnomaliesSchedule().operation()
        yield StatisticsSchedule().operation()

        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)

    @inlineCallbacks
    def test_delete(self):
        anomaly.pollute_Event_for_testing(3)
        yield AnomaliesSchedule().operation()
        yield StatisticsSchedule().operation()

        # be sure that AnomalyHistory is populated
        handler = self.request({}, role='admin')
        yield handler.get()
        self.assertEqual(len(self.responses), 1)
        self.assertTrue(isinstance(self.responses, list))

        self.responses = []

        # delete stats
        handler = self.request({}, role='admin')
        yield handler.delete()

        self.responses = []

        # test that AnomalyHistory is not populated anymore
        handler = self.request({}, role='admin')
        yield handler.get()
        self.assertEqual(len(self.responses), 0)
        self.assertTrue(isinstance(self.responses, list))
