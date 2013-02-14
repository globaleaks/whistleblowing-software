from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

from globaleaks import db
from globaleaks.settings import transact
from globaleaks.tests import helpers
from globaleaks.models import *
from globaleaks.transactors.asyncoperations import AsyncOperations
from globaleaks.transactors.crudoperations import CrudOperations


class TestEmail(helpers.TestHandler):
    @inlineCallbacks
    def setUp(self):
        self.setUp_dummy()
        yield db.createTables(create_node=True)
        yield self._setup_database()
        self.recipe = yield CrudOperations().new_submission({
                'wb_fields': {'city': 1, 'Sun': 2, 'dict2': 1, 'dict3': 1},
                'context_gus': self.ctx['context_gus'],
                'receivers': [self.rcv['receiver_gus']],
                'files': [],
                'finalize': True,
        })
        yield AsyncOperations().tip_creation()


    @transact
    def _setup_database(self, store):

        self.ctx = Context(self.dummyContext)
        self.rcv = Receiver(self.dummyReceiver)

        self.rcv['contexts'].append(self.ctx['context_gus'])
        self.rcv['notification_fields']['mail_address'] = 'maker@globaleaks.org'
        self.rcv['receiver_level'] = 1
        self.newrcv = Receiver(store).update(self.rcv['receiver_gus'], self.rcv)

        # Assign Receiver to the Context
        Receiver(store).receiver_align(self.rcv['receiver_gus'], [ self.ctx['context_gus'] ] )
        Context(store).full_context_align(self.rcv['receiver_gus'], [ self.ctx['context_gus']] )

        receiver_desc = Receiver(store).get_single(self.rcv['receiver_gus'])
        context_desc = Context(store).get_single(self.ctx['context_gus'])

        node = store.find(Node).one()
        node.notification_settings = {
                "server": "box549.bluehost.com",
                "port":25,
                "username":"sendaccount939@globaleaks.org",
                "password":"sendaccount939",
                "ssl": False
        }


    def test_sendmail(self):
        def success(*result):
            print 'message sent', result

        def failure(result):
            print 'failure', result

        d = AsyncOperations().tip_notification()
        return d




