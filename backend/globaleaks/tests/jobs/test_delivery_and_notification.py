# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs.delivery import Delivery
from globaleaks.jobs.notification import Notification
from globaleaks.tests import helpers


class TestNotification(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_notification(self):
        yield self.test_model_count(models.User, 8)

        yield self.test_model_count(models.InternalTip, 0)
        yield self.test_model_count(models.ReceiverTip, 0)
        yield self.test_model_count(models.InternalFile, 0)
        yield self.test_model_count(models.WhistleblowerFile, 0)
        yield self.test_model_count(models.Comment, 0)
        yield self.test_model_count(models.Message, 0)
        yield self.test_model_count(models.Mail, 0)

        yield self.perform_full_submission_actions()

        yield self.test_model_count(models.InternalTip, 2)
        yield self.test_model_count(models.ReceiverTip, 4)
        yield self.test_model_count(models.InternalFile, 4)
        yield self.test_model_count(models.ReceiverFile, 0)
        yield self.test_model_count(models.WhistleblowerFile, 0)
        yield self.test_model_count(models.Comment, 6)
        yield self.test_model_count(models.Message, 8)
        yield self.test_model_count(models.Mail, 0)

        yield Delivery().run()

        yield self.test_model_count(models.InternalTip, 2)
        yield self.test_model_count(models.ReceiverTip, 4)
        yield self.test_model_count(models.InternalFile, 4)
        yield self.test_model_count(models.ReceiverFile, 8)
        yield self.test_model_count(models.WhistleblowerFile, 0)
        yield self.test_model_count(models.Comment, 6)
        yield self.test_model_count(models.Message, 8)
        yield self.test_model_count(models.Mail, 0)

        notification = Notification()
        notification.skip_sleep = True

        yield notification.generate_emails()

        yield self.test_model_count(models.Mail, 4)

        yield notification.spool_emails()

        yield self.test_model_count(models.Mail, 0)
