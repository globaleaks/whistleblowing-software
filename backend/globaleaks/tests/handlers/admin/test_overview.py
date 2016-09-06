# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import overview
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.rest import requests
from globaleaks.tests import helpers


class TestTipsOverviewDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = overview.Tips

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()
        yield DeliverySchedule().operation()

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self.assertEqual(len(self.responses[0]), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.TipsOverviewDesc)


class TestFilesOverviewDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = overview.Files

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()
        yield DeliverySchedule().operation()

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        yield handler.get()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.FilesOverviewDesc)
