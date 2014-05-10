
from twisted.internet.defer import inlineCallbacks
from storm import exceptions

from globaleaks.tests import helpers

from globaleaks.settings import transact, transact_ro
from globaleaks.models import *
from globaleaks.utils.structures import Fields

class TestTransaction(helpers.TestGLWithPopulatedDB):

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

    def test_transaction_with_exception(self):
        yield self.assertFailure(self._transaction_with_exception(), Exception)

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
    def _transact_with_stuff(self, store):
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')
        receiver_user = User(self.dummyReceiverUser_1)
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']

        # Avoid receivers with the same username!
        receiver_user.username = unicode("xxx")

        store.add(receiver_user)
 
        receiver = Receiver(r)
        receiver.user_id = receiver_user.id
        receiver.gpg_key_status = Receiver._gpg_types[0] # this is a required field!
        receiver.mail_address = self.dummyReceiver_1['mail_address']
        store.add(receiver)

        return receiver.id

    @transact
    def _transact_with_stuff_failing(self, store):
        r = self.localization_set(self.dummyReceiver_1, Receiver, 'en')
        receiver_user = User(self.dummyReceiverUser_1)
        receiver_user.last_login = self.dummyReceiverUser_1['last_login']
        store.add(receiver_user)

        receiver = Receiver(r)
        receiver.user_id = receiver_user.id
        receiver.gpg_key_status = Receiver._gpg_types[0] # this is a required field!
        receiver.mail_address = self.dummyReceiver_1['mail_address']
        store.add(receiver)

        raise exceptions.DisconnectionError

    @transact_ro
    def _transact_ro_add_context(self, store):
        c = self.localization_set(self.dummyContext, Context, 'en')
        context = Context(c)

        fo = Fields()
        fo.update_fields('en', self.dummyContext['fields'])
        fo.context_import(context)

        context.tags = self.dummyContext['tags']
        context.submission_timetolive = context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = { "en" : u'Localized723' }
        store.add(context)
        return context.id

    @transact_ro
    def _transact_ro_context_bla_bla(self, store, context_id):
        self.assertEqual(store.find(Context, Context.id == context_id).one(), None)

    @inlineCallbacks
    def test_transact_ro(self):
        created_id = yield self._transact_ro_add_context()
        yield self._transact_ro_context_bla_bla(created_id)