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


class TestEmail(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def test_sendmail(self):
        yield NotificationSchedule().operation()

        wb_steps = yield helpers.fill_random_fields(self.dummyContext['id'])

        self.recipe = yield submission.create_submission({
            'wb_steps': wb_steps,
            'context_id': self.dummyContext['id'],
            'receivers': [self.dummyReceiver_1['id']],
            'files': [],
            'finalize': True,
            }, True, 'en')

        yield delivery_sched.tip_creation()

        aps1 = NotificationSchedule()

        yield aps1.operation()

        # TODO to be completed with real tests.
        #      now we simply perform operations to raise code coverage
