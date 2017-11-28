# -*- coding: utf-8 -*-
from globaleaks.models import Counter
from globaleaks.orm import get_store, transact, TenantIterator
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class MockStormResult(object):
    def __init__(self, tid):
        self.tid = tid

    def __repr__(self):
        return '<msr[{}] {}>'.format(self.tid, str(id(self))[-4:])


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

    def db_add_config(self, store):
        store.add(Counter({'key': 'antani', 'number': 31337}))

    @transact
    def _transact_with_success(self, store):
        self.db_add_config(store)

    @transact
    def _transact_with_exception(self, store):
        self.db_add_config(store)
        raise Exception("antani")

    def test_tenant_iterator(self):
        f = MockStormResult

        input_lst = [f(1), f(1), f(1), f(2), f(2), f(3), f(5), f(7), f(7), f(2), f(1)]
        output_lst = [f.tid for f in TenantIterator(input_lst)]

        expected_sets = [{1,2,3,5,7}, {1,2,7}, {1,2}, {1}]

        for s in expected_sets:
            output_g = set(output_lst[:len(s)])
            output_lst = output_lst[len(s):]

            self.assertEqual(output_g, s) 

        self.assertFalse(output_lst)

    def test_transaction_pragmas(self):
        return self._transaction_pragmas()

    @inlineCallbacks
    def test_transact_with_stuff(self):
        yield self._transact_with_success()

        # now check data actually written
        store = get_store()
        self.assertEqual(store.find(Counter).count(), 1)

    @inlineCallbacks
    def test_transaction_with_exception(self):
        store = get_store()
        count1 = store.find(Counter).count()

        yield self.assertFailure(self._transact_with_exception(), Exception)

        count2 = store.find(Counter).count()

        self.assertEqual(count1, count2)

    def test_transact_decorate_function(self):
        @transact
        def transaction(store):
            self.assertTrue(getattr(store, 'find'))

        return transaction()
