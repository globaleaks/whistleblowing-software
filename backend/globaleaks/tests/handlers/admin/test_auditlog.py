# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import auditlog
from globaleaks.tests import helpers


class TestTipsCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = auditlog.TipsCollection

    @inlineCallbacks
    def test_get(self):
        yield self.perform_full_submission_actions()

        handler = self.request({}, role='admin')
        response = yield handler.get()

        self.assertTrue(isinstance(response, list))
        self.assertEqual(len(response), 2)


class TestJobsTiming(helpers.TestHandler):
    _handler = auditlog.JobsTiming

    @inlineCallbacks
    def test_get(self):
        handler = self.request({}, role='admin')

        yield handler.get()
