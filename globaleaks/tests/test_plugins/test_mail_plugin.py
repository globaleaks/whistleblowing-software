from twisted.trial import unittest

from globaleaks import db
from globaleaks.settings import transact
from globaleaks.models.receiver import Receiver
from globaleaks.tests import helpers
from globaleaks.models.context import Context
from globaleaks.transactors.crudoperations import CrudOperations

class TestEmail(helpers.TestHandler):
    def setUp(self):
        yield db.createTables(create_node=False)
        yield self._setup_database()
        yield CrudOperations().new_submission({
                'wb_fields': {},
                'context_gus': self.ctx['context_gus'],
                'receivers': [self.rcv['receiver_gus']],
                'files': [],
                'finalize': True,
        })

    @transact
    def _setup_database(self):
        self.ctx = Context(self.store).new(helpers.dummyContext)
        self.rcv = Recever(self.store).new(helpers.dummyReceiver)
        self.rcv.context.append(self.ctx['context_gus'])

        Recever(self.store).update(self.rcv['receiver_gus'], selv.rcv)

    def test_sendmail(self):
        pass



