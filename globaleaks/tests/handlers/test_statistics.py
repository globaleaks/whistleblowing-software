# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests
from globaleaks.tests import helpers
from globaleaks.handlers import statistics
from globaleaks.settings import GLSetting
from globaleaks.jobs.statistics_sched import AnomaliesSchedule, StatisticsSchedule

class TestAnomaliesCollection(helpers.TestHandler):
    _handler = statistics.AnomaliesCollection

    @inlineCallbacks
    def test_get(self):
        GLSetting.anomalies_counter['new_submission'] = 1000
        GLSetting.anomalies_counter['finalized_submission'] = 1000
        GLSetting.anomalies_counter['anon_requests'] = 1000
        GLSetting.anomalies_counter['file_uploaded'] = 1000

        AnomaliesSchedule().operation()

        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 4)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.AnomaliesCollection)

class TestStatsCollection(helpers.TestHandler):
    _handler = statistics.StatsCollection

    @inlineCallbacks
    def test_get(self):

        StatisticsSchedule().operation()

        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.StatsCollection)
