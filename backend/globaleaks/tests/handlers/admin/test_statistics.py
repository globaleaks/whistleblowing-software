# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import anomaly
from globaleaks.handlers.admin import statistics
from globaleaks.jobs.statistics_sched import AnomaliesSchedule, StatisticsSchedule
from globaleaks.models import Stats
from globaleaks.orm import transact
from globaleaks.tests import helpers


class TestStatsCollection(helpers.TestHandler):
    _handler = statistics.StatsCollection

    @transact
    def get_stats_count(self, store):
        return store.find(Stats).count()

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        response = yield handler.get(0)

        self.assertEqual(len(response), 3)
        self.assertEqual(len(response['heatmap']), 7 * 24)

        self.pollute_events(10)

        yield AnomaliesSchedule().run()
        yield StatisticsSchedule().run()

        for i in range(2):
            handler = self.request({}, role='admin')
            response = yield handler.get(i)
            self.assertEqual(len(response), 3)
            self.assertEqual(len(response['heatmap']), 7 * 24)


class TestAnomalyCollection(helpers.TestHandler):
    _handler = statistics.AnomalyCollection

    @inlineCallbacks
    def test_get(self):
        self.pollute_events(10)

        yield AnomaliesSchedule().run()
        yield StatisticsSchedule().run()

        handler = self.request({}, role='admin')
        response = yield handler.get()

        # be sure that AnomalyHistory is populated
        self.assertTrue(isinstance(response, list))
        self.assertEqual(len(response), 1)


class TestRecentEventsCollection(helpers.TestHandler):
    _handler = statistics.RecentEventsCollection

    @inlineCallbacks
    def test_get(self):
        self.pollute_events(3)

        yield StatisticsSchedule().run()

        handler = self.request({}, role='admin')

        response = yield handler.get('details')
        self.assertTrue(isinstance(response, list))

        for k in ['id', 'duration', 'event', 'creation_date']:
            for elem in response:
                self.assertTrue(k in elem)

        response = yield handler.get('summary')
        self.assertTrue(isinstance(response, dict))

        for k in anomaly.ANOMALY_MAP:
            self.assertTrue(k in response)


class TestJobsTiming(helpers.TestHandler):
    _handler = statistics.JobsTiming

    @inlineCallbacks
    def test_get(self):
        # TODO: start job mocking the reactor

        handler = self.request({}, role='admin')

        yield handler.get()
