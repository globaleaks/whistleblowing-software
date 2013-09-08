from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

# override GLsetting
from globaleaks.settings import GLSetting, transact, transact_ro

GLSetting.notification_plugins = ['MailNotification']
GLSetting.memory_copy.notif_source_name = "name fake"
GLSetting.memory_copy.notif_source_email = "mail@fake.xxx"

from globaleaks.tests import helpers
from globaleaks import models
from globaleaks.handlers import submission
from globaleaks.jobs import delivery_sched
from globaleaks.jobs.notification_sched import APSNotification
from globaleaks.plugins import notification

class TestEmail(helpers.TestGL):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        self.recipe = yield submission.create_submission({
            'wb_fields': helpers.fill_random_fields(self.dummyContext),
            'context_gus': self.dummyContext['context_gus'],
            'receivers': [self.dummyReceiver['receiver_gus']],
            'files': [],
            'finalize': True,
            }, finalize=True)
        yield delivery_sched.tip_creation()

        # This mocks out the MailNotification plugin so it does not actually
        # require to perform a connection to send an email.
        # XXX we probably want to create a proper mock of the ESMTPSenderFactory
        def mail_flush_mock(self, from_address, to_address, message_file, event):
            return defer.succeed(None)

        notification.MailNotification.mail_flush = mail_flush_mock

    @transact
    def _setup_database(self, store):
        del self.dummyContext['receivers']
        self.ctx = models.Context(self.dummyContext)
        del self.dummyReceiver['contexts']
        self.rcv = models.Receiver(self.dummyReceiver)
        store.add(self.ctx)
        store.add(self.rcv)
        store.commit()

        self.rcv.notification_fields['mail_address'] = 'vecna@globaleaks.org'
        self.rcv.receiver_level = 1

        # Assign Receiver to the Context
        self.ctx.receivers.add(self.rcv)

    @inlineCallbacks
    def test_sendmail(self):
        def success(*result):
            print 'message sent', result
            self.assertTrue(True)

        def failure(result):
            print 'failure', result
            self.assertTrue(False)

        aps = APSNotification()
        aps.notification_settings = {
            "server": "mail.headstrong.de",
            "port": 587,
            "username": "sendaccount@lists.globaleaks.org",
            "password": "sendaccount99",
            "source_name" : "Unit Test Name",
            "source_email" : "unit@test.mail",
            "tip_template": { "en" : u"tip tip"},
            "file_template": { "en" : u"file file"},
            "activation_template": { "en" : u"activation activation"},
            "comment_template": { "en" : u"comment comment"},
            "tip_mail_title": { "en" : u'title tip'},
            "comment_mail_title": { "en" : u'title comment'},
            "file_mail_title": { "en" : u'title file'} ,
            "security": u'TLS',
        }

        tip_events = yield aps.create_tip_notification_events()
        yield aps.do_tip_notification(tip_events)

