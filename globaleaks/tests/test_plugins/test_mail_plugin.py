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

settings.plugins = ['MailNotification']
from twisted.python import log
import sys
log.startLogging(sys.stdout)

class TestEmail(helpers.TestHandler):
    @inlineCallbacks
    def setUp(self):
        self.setUp_dummy()
        yield db.createTables(create_node=True)
        yield self._setup_database()
        self.recipe = yield submission.create_submission({
                'wb_fields': {'city': 1, 'Sun': 2, 'dict2': 1, 'dict3': 1},
                'context_gus': self.ctx.id,
                'receivers': self.rcv.id,
                'files': [],
                'finalize': True,
        })
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

        self.rcv.notification_fields['mail_address'] = '@globaleaks.org'
        self.rcv.receiver_level = 1

        # Assign Receiver to the Context
        self.ctx.receivers.add(self.rcv)

        node = store.find(Node).one()
        node.notification_settings["server"] = "box549.bluehost.com"
        node.notification_settings["port"] = 25
        node.notification_settings["username"] ="sendaccount939@globaleaks.org"
        node.notification_settings["password"] ="sendaccount939"
        node.notification_settings["ssl"] = False


    def test_sendmail(self):
        def success(*result):
            print 'message sent', result

        def failure(result):
            print 'failure', result

        d = APSNotification().tip_notification()
        d.addBoth(success, failure)
        return d




