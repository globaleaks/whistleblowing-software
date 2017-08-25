from globaleaks.models import *
from globaleaks.orm import get_store
from globaleaks.tests import helpers
from globaleaks.utils.utility import datetime_null
from twisted.internet.defer import inlineCallbacks


class TestORM(helpers.TestGL):
    initialize_test_database_using_archived_db = False

    @transact
    def _transaction_with_exception(self, store):
        raise Exception

    @transact
    def _transaction_pragmas(self, store):
        # Verify setting enabled in the sqlite db
        self.assertEqual(store.execute("PRAGMA foreign_keys").get_one()[0], 1)  # ON
        self.assertEqual(store.execute("PRAGMA secure_delete").get_one()[0], 1) # ON
        self.assertEqual(store.execute("PRAGMA auto_vacuum").get_one()[0], 1)   # FULL

    def db_add_receiver(self, store):
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')
        receiver_user = User(self.dummyReceiverUser_1)
        receiver_user.password = self.dummyReceiverUser_1['password']
        receiver_user.salt = self.dummyReceiverUser_1['salt']
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']
        receiver_user.password_change_needed = self.dummyReceiverUser_1['password_change_needed']
        receiver_user.password_change_date = datetime_null()
        receiver_user.mail_address = self.dummyReceiverUser_1['mail_address']

        # Avoid receivers with the same username!
        receiver_user.username = unicode("xxx")

        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user_id = receiver_user.id
        store.add(receiver)

        # Set receiver.id = receiver.user.username = receiver_user.id
        receiver.id = receiver_user.username = receiver_user.id

        return receiver.id

    @transact
    def _transact_with_success(self, store):
        self.db_add_receiver(store)

    @transact
    def _transact_with_exception(self, store):
        self.db_add_receiver(store)
        raise Exception("antani")

    def test_transaction_pragmas(self):
        return self._transaction_pragmas()

    @inlineCallbacks
    def test_transact_with_stuff(self):
        yield self._transact_with_success()

        # now check data actually written
        store = get_store()
        self.assertEqual(store.find(Receiver).count(), 1)

    @inlineCallbacks
    def test_transaction_with_exception(self):
        store = get_store()
        count1 = store.find(Receiver).count()

        yield self.assertFailure(self._transact_with_exception(), Exception)

        store = get_store()
        count2 = store.find(Receiver).count()

        self.assertEqual(count1, count2)

    @inlineCallbacks
    def test_transact_decorate_function(self):
        @transact
        def transaction(store):
            self.assertTrue(getattr(store, 'find'))

        yield transaction()
