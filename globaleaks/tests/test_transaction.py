import os

from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks
from storm import exceptions

from globaleaks.settings import transact, get_store
from globaleaks import settings
from globaleaks.models.context import Context
from globaleaks.models.receiver import Receiver
from globaleaks.tests import helpers
from globaleaks.db import createTables


class TestTransaction(unittest.TestCase):
    @inlineCallbacks
    def setUp(self):
        self.id = None
        yield createTables(create_node=False)

    def tearDown(self):
        os.unlink(settings.db_file[len('sqlite:///'):])

    def test_transaction_with_exception(self):
        return self.assertFailure(self._transaction_with_exception(), Exception)

    def test_transaction_ok(self):
        return self._transaction_ok()

    def test_transaction_with_commit_close(self):
        return self._transaction_with_commit_close()

    @inlineCallbacks
    def test_transact_with_stuff(self):
        yield self._transact_with_stuff()
        # now check data actually written
        store = get_store()
        self.assertEqual(store.find(Receiver, Receiver.receiver_gus == self.id).count(),
                         1)


    @inlineCallbacks
    def test_transact_with_stuff_failing(self):
        yield self._transact_with_stuff_failing()
        store = get_store()
        self.assertEqual(list(store.find(Context, Context.context_gus == self.id)),
                         [])


    @transact
    def _transaction_with_exception(self, store):
        raise Exception

    #def transaction_with_exception_while_writing(self):
    @transact
    def _transaction_ok(self, store):
        store
        return

    @transact
    def _transaction_with_commit_close(self, store):
        store.commit()
        store.close()

    @transact
    def _transact_with_stuff(self, store):
       self.id = Receiver(store).new(helpers.dummyReceiver)['receiver_gus']


    @transact
    def _transact_with_stuff_failing(self, store):
        self.id = Context(store).new(helpers.dummyContext)['context_gus']
        raise exceptions.DisconnectionError
