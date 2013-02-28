from globaleaks import settings
from globaleaks.settings import transact
from globaleaks.tests import helpers
from globaleaks import models
from globaleaks.handlers import submission
from globaleaks.jobs import delivery_sched
from globaleaks.jobs.notification_sched import APSNotification
from twisted.internet.defer import inlineCallbacks

settings.notification_plugins = ['MailNotification']

class TestEmail(helpers.TestGL):

    @inlineCallbacks
    def setUp(self):
        helpers.TestGL.setUp(self)

        yield self.initialize_db()
        self.recipe = yield submission.create_submission({
            'wb_fields': {'city': 1, 'Sun': 2, 'dict2': 1, 'dict3': 1},
            'context_gus': self.dummyContext['context_gus'],
            'receivers': [self.dummyReceiver['receiver_gus']],
            'files': [],
            'finalize': True,
            }, finalize=True)
        yield delivery_sched.tip_creation()


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


    def test_sendmail(self):
        def success(*result):
            print 'message sent', result

        def failure(result):
            print 'failure', result

        notification_settings = {
            "server": "box549.bluehost.com",
            "port": 25,
            "username": "sendaccount939@globaleaks.org",
            "password": "sendaccount939",
            "tip_template": "tip tip",
            "file_template": "file file",
            "activation_template": "activation activation",
            "comment_template": "comment comment",
            "security": 'TLS',
            }

        d = APSNotification().do_tip_notification(notification_settings)
        return d

