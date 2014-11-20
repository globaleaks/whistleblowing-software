from twisted.internet.defer import inlineCallbacks

# override GLsetting
from globaleaks.settings import GLSetting

GLSetting.notification_plugins = ['MailNotification']
GLSetting.memory_copy.notif_source_name = "name fake"
GLSetting.memory_copy.notif_source_email = "mail@fake.xxx"

from globaleaks.tests import helpers
from globaleaks.handlers import submission
from globaleaks.jobs import delivery_sched
from globaleaks.jobs.notification_sched import NotificationSchedule

class TestEmail(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)

        fields = yield helpers.fill_random_fields(self.dummyContext)

        self.recipe = yield submission.create_submission({
            'wb_fields': fields,
            'context_id': self.dummyContext['id'],
            'receivers': [self.dummyReceiver_1['id']],
            'files': [],
            'finalize': True,
            }, finalize=True)

        yield delivery_sched.tip_creation()

    @inlineCallbacks
    def test_sendmail(self):
        aps = NotificationSchedule()
        aps.notification_settings = {
            "server": "mail.headstrong.de",
            "port": 587,
            "username": "sendaccount@lists.globaleaks.org",
            "password": "sendaccount99",
            "source_name" : "Unit Test Name",
            "source_email" : "unit@test.mail",
            "security": u'TLS',
            "encrypted_tip_template": { "en" : u"E tip template "},
            "encrypted_tip_mail_title": { "en" : u"E tip subj "},
            "plaintext_tip_template": { "en" : u"P tip template"},
            "plaintext_tip_mail_title": { "en" : u"P tip subj"},
            "file_template": { "en" : u"file file"},
            "file_mail_title": { "en" : u'title file'} ,
            "comment_template": { "en" : u"comment comment"},
            "comment_mail_title": { "en" : u'title comment'},
            "message_template" : { "en": u"message template" },
            "message_mail_title" : { "en" : u"msg mail title" },
        }

        # 100 as limit
        (tip_events, enqueued) = yield aps.create_tip_notification_events(0)
        self.assertEqual(enqueued, 2)

        yield aps.do_tip_notification(tip_events)

