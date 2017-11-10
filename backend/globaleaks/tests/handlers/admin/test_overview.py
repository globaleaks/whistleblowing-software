# -*- coding: utf-8 -*-
import json

from globaleaks.handlers.admin import overview
from globaleaks.jobs.delivery import Delivery
from globaleaks.rest import requests
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestTipsOverviewDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = overview.Tips

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()
        yield Delivery().run()

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), self.population_of_submissions)
        self._handler.validate_message(json.dumps(response), requests.TipsOverviewDesc)


class TestFilesOverviewDesc(helpers.TestHandlerWithPopulatedDB):
    _handler = overview.Files

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()
        yield Delivery().run()

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')
        response = yield handler.get()

        self._handler.validate_message(json.dumps(response), requests.FilesOverviewDesc)
