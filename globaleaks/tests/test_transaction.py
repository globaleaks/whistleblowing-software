from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks
from storm import exceptions

from globaleaks.settings import transact
from globaleaks.models import Comment

class TestTransaction(unittest.TestCase):

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
        comment_id = yield self._transact_with_stuff()
        # now check data actually written
        store = transact.get_store()
        self.assertEqual(store.find(Comment, Comment.id == comment_id).count(), 1)

    @inlineCallbacks
    def test_transact_with_stuff_failing(self):
        comment_id = yield self._transact_with_stuff_failing()
        store = transact.get_store()
        self.assertEqual(list(store.find(Comment, Comment.id == comment_id)), [])

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
        comment = Comment()
        comment.author = comment.internaltip_id = comment.type = comment.content = "receiver"
        # just something not NULL
        store.add(comment)
        return comment.id

    @transact
    def _transact_with_stuff_failing(self, store):
        comment = Comment()
        comment.author = comment.internaltip_id = comment.type = comment.content = "receiver"
        # just something not NULL
        store.add(comment)
        raise exceptions.DisconnectionError

