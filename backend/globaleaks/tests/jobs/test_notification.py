# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs.delivery import Delivery
from globaleaks.jobs.notification import Notification
from globaleaks.tests import helpers


class TestNotification(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_notification(self):
        yield self.test_model_count(models.Mail, 0)

        yield Delivery().run()

        notification = Notification()
        notification.skip_sleep = True
        yield notification.run()

        yield self.test_model_count(models.Mail, 0)
