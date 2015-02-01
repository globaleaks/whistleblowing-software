from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks.handlers import submission
from globaleaks.jobs import delivery_sched
from globaleaks.jobs.mailflush_sched import MailflushSchedule
from globaleaks.jobs.notification_sched import NotificationSchedule
from globaleaks.settings import GLSetting

class TestNotificationSchedule(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)
        yield self.perform_submission()

    @inlineCallbacks
    def test_notification_schedule(self):
        yield NotificationSchedule().operation()

        mail_schedule = MailflushSchedule()
        mail_schedule.skip_sleep = True
        yield mail_schedule.operation()

        # TODO to be completed with real tests.
        #      now we simply perform operations to raise code coverage
