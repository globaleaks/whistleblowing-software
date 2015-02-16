# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks
from twisted.internet import task

from globaleaks import anomaly
from globaleaks.handlers.admin import statistics
from globaleaks.jobs.statistics_sched import AnomaliesSchedule, StatisticsSchedule
from globaleaks.models import Stats
from globaleaks.settings import transact_ro
from globaleaks.tests import helpers
from globaleaks.tests.test_anomaly import pollute_events_for_testing
from globaleaks.utils.utility import datetime_now

anomaly.reactor = task.Clock()
StatisticsSchedule.collection_start_datetime = datetime_now()

class TestAnomaliesCollection(helpers.TestHandler):
    _handler = statistics.AnomaliesCollection

    @inlineCallbacks
    def test_get(self):
        pollute_events_for_testing(3)
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
        self.assertEqual(len(self.responses[0]), 3)
        self.assertEqual(len(self.responses[0]['heatmap']), 7 * 24)

        pollute_events_for_testing(3)

        yield AnomaliesSchedule().operation()
        yield StatisticsSchedule().operation()

        for i in range(0, 2):
            handler = self.request({}, role='admin')
            yield handler.get(i)
            self.assertEqual(len(self.responses[1 + i]), 3)
            self.assertEqual(len(self.responses[1 + i]['heatmap']), 7 * 24)

    @inlineCallbacks
    def test_delete(self):
        pollute_events_for_testing(3)
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
        pollute_events_for_testing(3)
        yield AnomaliesSchedule().operation()
        yield StatisticsSchedule().operation()

        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)

    @inlineCallbacks
    def test_delete(self):
        pollute_events_for_testing(3)
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


class TestRecentEventsCollection(helpers.TestHandler):
    _handler = statistics.RecentEventsCollection

    @inlineCallbacks
    def test_get(self):
        pollute_events_for_testing(3)
        yield StatisticsSchedule().operation()

        handler = self.request({}, role='admin')

        yield handler.get('details')
        yield handler.get('summary')

        self.assertTrue(isinstance(self.responses[0], list))
        self.assertTrue(isinstance(self.responses[1], dict))

        for k in ['id', 'duration', 'event', 'creation_date']:
            for elem in self.responses[0]:
                self.assertTrue(k in elem)

        for k in ['wb_messages', 'wb_comments',
                  'receiver_messages', 'receiver_comments',
                  'started_submissions', 'completed_submissions',
                  'successful_logins', 'failed_logins',
                  'uploaded_files', 'appended_files']:
            self.assertTrue(k in self.responses[1])
