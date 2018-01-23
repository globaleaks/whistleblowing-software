# -*- coding: utf-8 -*-
from globaleaks.models import Counter
from globaleaks.orm import get_session, transact
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestORM(helpers.TestGL):
    initialize_test_database_using_archived_db = False

    @transact
    def _verify_pragmas(self, session):
        # Verify setting enabled in the sqlite db
        self.assertEqual(session.execute("PRAGMA foreign_keys").fetchone()[0], 1)  # ON
        self.assertEqual(session.execute("PRAGMA secure_delete").fetchone()[0], 1) # ON
        self.assertEqual(session.execute("PRAGMA auto_vacuum").fetchone()[0], 1)   # FULL

    @transact
    def _transact_with_success(self, session):
        self.db_add_config(session)

    @transact
    def _transact_with_exception(self, session):
        self.db_add_config(session)
        raise Exception("antani")

    def db_add_config(self, session):
        session.add(Counter({'tid': 1, 'key': 'antani', 'number': 31337}))

    @inlineCallbacks
    def test_pragmas(self):
        yield self._verify_pragmas()

    @inlineCallbacks
    def test_transact_with_stuff(self):
        yield self._transact_with_success()

        # now check data actually written
        session = get_session()
        self.assertEqual(session.query(Counter).count(), 1)

    @inlineCallbacks
    def test_transaction_with_exception(self):
        session = get_session()
        count1 = session.query(Counter).count()

        yield self.assertFailure(self._transact_with_exception(), Exception)

        count2 = session.query(Counter).count()

        self.assertEqual(count1, count2)

    def test_transact_decorate_function(self):
        @transact
        def transaction(session):
            self.assertTrue(getattr(session, 'query'))

        return transaction()
