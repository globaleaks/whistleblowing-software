from twisted.internet.defer import inlineCallbacks, fail

from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.jobs.notification_sched import NotificationSchedule

from globaleaks.tests import helpers
from globaleaks.tests.jobs.test_base import get_scheduled_email_count


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

        def sendmail(x, y, z):
            return fail(True)

        notification_schedule.sendmail = sendmail

        for i in range(0, 10):
            yield notification_schedule.run()

            count = yield get_scheduled_email_count()
            self.assertEqual(count, 28)

        yield notification_schedule.run()

        count = yield get_scheduled_email_count()
        self.assertEqual(count, 0)
