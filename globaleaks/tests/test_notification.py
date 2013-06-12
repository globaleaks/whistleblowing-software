# ovverride GLsetting
from globaleaks.settings import GLSetting, transact
from globaleaks.tests import helpers

from globaleaks import settings
from globaleaks import models
from globaleaks.handlers import submission
from globaleaks.jobs import delivery_sched
from globaleaks.jobs.notification_sched import APSNotification
from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

from globaleaks.plugins import notification

GLSetting.notification_plugins = ['MailNotification']

class TestEmail(helpers.TestGL):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        self.recipe = yield submission.create_submission({
            'wb_fields': helpers.MockDict().fill_random_fields(self.dummyContext),
            'context_gus': self.dummyContext['context_gus'],
            'receivers': [self.dummyReceiver['receiver_gus']],
            'files': [],
            'finalize': True,
            }, finalize=True)
        yield delivery_sched.tip_creation()

        # This mocks out the MailNotification plugin so it does not actually
        # require to perform a connection to send an email.
        # XXX we probably want to create a proper mock of the ESMTPSenderFactory
        def sendmail_mock(self, authentication_username, authentication_password, from_address,
                          to_address, message_file, smtp_host, smtp_port, security, event):
            return defer.succeed(None)

        notification.MailNotification.sendmail = sendmail_mock

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

        def failure(result):
            print 'failure', result

        aps = APSNotification()
        aps.notification_settings = {
            "server": "box549.bluehost.com",
            "port": 25,
            "username": "sendaccount939@globaleaks.org",
            "password": "sendaccount939",
            "tip_template": u"tip tip",
            "file_template": u"file file",
            "activation_template": u"activation activation",
            "comment_template": u"comment comment",
            "tip_mail_title": u'title tip',
            "comment_mail_title": u'title comment',
            "file_mail_title": u'title file',
            "security": u'TLS',
        }

        tip_events = yield aps.create_tip_notification_events()
        yield aps.do_tip_notification(tip_events)

