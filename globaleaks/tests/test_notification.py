

@transact
def systemsetting_setup(self, store):
    node = store.find(models.Node).one()
    node.notification_settings["server"] = "box549.bluehost.com"
    node.notification_settings["port"] = 25
    node.notification_settings["username"] ="sendaccount939@globaleaks.org"
    # node.notification_settings["password"] ="sendaccount939"
    node.notification_settings["password"] ="wrong"
    # XXX - I don't want a mail every check
    node.notification_settings["ssl"] = False

@inlineCallbacks
def test_sendmail_wrongconf(self):
    # Currently disabled, checks password few line over here
    self.dummyReceiver['notification_fields']['mail_address'] = 'vecna@globaleaks.org'
    self.dummyReceiver['receiver_level'] = 1
    yield self.systemsetting_setup()

    delivery_sched.tip_creation()
    APSNotification().operation()










from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

from globaleaks import db
from globaleaks import settings
from globaleaks.settings import transact
from globaleaks.tests import helpers
from globaleaks.models import *
from globaleaks.handlers import submission
from globaleaks.jobs import delivery_sched
from globaleaks.jobs.notification_sched import APSNotification

settings.notification_plugins = ['MailNotification']
from twisted.python import log


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
        self.ctx = Context(self.dummyContext)
        del self.dummyReceiver['contexts']
        self.rcv = Receiver(self.dummyReceiver)
        store.add(self.ctx)
        store.add(self.rcv)
        store.commit()

        self.rcv.notification_fields['mail_address'] = 'maker@globaleaks.org'
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
            "email_template": "{} {} %s foo",
            "ssl": False,
            }
        d = APSNotification().do_tip_notification(notification_settings)
        return d



