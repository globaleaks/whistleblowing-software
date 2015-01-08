from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import submission
from globaleaks.jobs import delivery_sched
from globaleaks.jobs.notification_sched import NotificationSchedule

# override GLsetting
from globaleaks.settings import GLSetting
GLSetting.notification_plugins = ['MailNotification']
GLSetting.memory_copy.notif_source_name = "name fake"
GLSetting.memory_copy.notif_source_email = "mail@fake.xxx"


class TestNotificationSchedule(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)
        yield self.perform_submission()

    @inlineCallbacks
    def test_notification_schedule(self):
        aps = NotificationSchedule()

        yield aps.operation()

        # TODO to be completed with real tests.
        #      now we simply perform operations to raise code coverage
