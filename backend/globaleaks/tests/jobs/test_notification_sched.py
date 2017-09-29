# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks, succeed

from globaleaks import models
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.jobs.notification_sched import NotificationSchedule
from globaleaks.tests import helpers


class TestNotificationSchedule(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_notification_schedule_success(self):
        yield self.test_model_count(models.Mail, 0)

        yield DeliverySchedule().run()

        notification_schedule = NotificationSchedule()
        notification_schedule.skip_sleep = True
        yield notification_schedule.run()

        yield self.test_model_count(models.Mail, 0)

    @inlineCallbacks
    def test_notification_schedule_failure(self):
        yield self.test_model_count(models.Mail, 0)

        yield DeliverySchedule().run()

        notification_schedule = NotificationSchedule()
        notification_schedule.skip_sleep = True

        def sendmail_failure(_):
            # simulate the failure just returning with no action
            return succeed(None)

        notification_schedule.sendmail = sendmail_failure

        for _ in range(10):
            yield notification_schedule.run()
            yield self.test_model_count(models.Mail, 24)


        yield notification_schedule.run()

        yield self.test_model_count(models.Mail, 0)
