from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.jobs.notification_sched import NotificationSchedule
from globaleaks.tests import helpers
from globaleaks.tests.jobs.test_base import get_scheduled_email_count
from twisted.internet.defer import inlineCallbacks, succeed


class TestNotificationSchedule(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)
        yield self.perform_full_submission_actions()

    @inlineCallbacks
    def test_notification_schedule_success(self):
        count = yield get_scheduled_email_count()
        self.assertEqual(count, 0)

        yield DeliverySchedule().run()

        notification_schedule = NotificationSchedule()
        notification_schedule.skip_sleep = True
        yield notification_schedule.run()

        count = yield get_scheduled_email_count()
        self.assertEqual(count, 0)

    @inlineCallbacks
    def test_notification_schedule_failure(self):
        count = yield get_scheduled_email_count()
        self.assertEqual(count, 0)

        yield DeliverySchedule().run()

        notification_schedule = NotificationSchedule()
        notification_schedule.skip_sleep = True

        def sendmail_failure(_):
            # simulate the failure just returning with no action
            return succeed(None)

        notification_schedule.sendmail = sendmail_failure

        for _ in range(10):
            yield notification_schedule.run()

            count = yield get_scheduled_email_count()
            self.assertEqual(count, 28)

        yield notification_schedule.run()

        count = yield get_scheduled_email_count()
        self.assertEqual(count, 0)
