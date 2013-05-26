
from twisted.internet.defer import inlineCallbacks
from storm import exceptions

from globaleaks.tests import helpers

from globaleaks.settings import transact
from globaleaks.models import Receiver

class TestTransaction(helpers.TestGL):

    def test_transaction_with_exception(self):
        try:
            yield self._transaction_with_exception()
            self.assertTrue(False)
        except Exception:
            self.assertTrue(True)

    def test_transaction_ok(self):
        return self._transaction_ok()

    def test_transaction_with_commit_close(self):
        return self._transaction_with_commit_close()

    @inlineCallbacks
    def test_transact_with_stuff(self):
        receiver_id = yield self._transact_with_stuff()
        # now check data actually written
        store = transact.get_store()
        self.assertEqual(store.find(Receiver, Receiver.id == receiver_id).count(), 1)

    @inlineCallbacks
    def test_transact_with_stuff_failing(self):
        receiver_id = yield self._transact_with_stuff_failing()
        store = transact.get_store()
        self.assertEqual(list(store.find(Receiver, Receiver.id == receiver_id)), [])

    @inlineCallbacks
    def test_transact_decorate_function(self):
        @transact
        def transaction(store):
            self.assertTrue(getattr(store, 'find'))
        yield transaction()

    @transact
    def _transaction_with_exception(self, store):
        raise Exception

    #def transaction_with_exception_while_writing(self):
    @transact
    def _transaction_ok(self, store):
        self.assertTrue(getattr(store, 'find'))
        return

    @transact
    def _transaction_with_commit_close(self, store):
        store.commit()
        store.close()

    @transact
    def _transact_with_stuff(self, store):
        try:
            receiver = Receiver(self.dummyReceiver)
            receiver.password = self.dummyReceiver['password']
            receiver.username = self.dummyReceiver['notification_fields']['mail_address']
            receiver.failed_login = 0
            receiver.notification_fields = self.dummyReceiver['notification_fields']
            store.add(receiver)
        except Exception as e:
            print e
        return receiver.id

    @transact
    def _transact_with_stuff_failing(self, store):
        receiver = Receiver(self.dummyReceiver)
        receiver.password = self.dummyReceiver['password']
        receiver.username = self.dummyReceiver['notification_fields']['mail_address']
        receiver.failed_login = 0
        receiver.notification_fields = self.dummyReceiver['notification_fields']
        store.add(receiver)
        raise exceptions.DisconnectionError

