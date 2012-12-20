import os

from twisted.internet import defer
from twisted.trial.unittest import TestCase

from storm.twisted.testing import FakeThreadPool
from storm.twisted.transact import transact, Transactor

from storm.locals import Int, Unicode
from storm.databases.sqlite import SQLite
from storm.uri import URI

import transaction
from storm.zope.zstorm import ZStorm

createQuery = "CREATE TABLE test"\
              "(id INTEGER PRIMARY KEY, colInt INTEGER, colUnicode VARCHAR)"


class DummyModel(object):
    __storm_table__ = 'test'

    id = Int(primary=True)
    colInt = Int()
    colUnicode = Unicode()

    zstorm = None

    def getStore(self):
        return self.zstorm.get('testDB')

    @transact
    def save(self):
        store = self.getStore()
        store.add(self)

    @transact
    def find(self):
        store = self.getStore()
        res = store.find(DummyModel,
            DummyModel.colInt == 42).one()
        return res

class BaseZStormTestCase(TestCase):
    def setUp(self):
        self.zstorm = ZStorm()

        self.threadpool = FakeThreadPool()
        self.transactor = Transactor(self.threadpool)

        # XXX use storm.tests.mocker
        # See storm.tests.twisted.transaction for an example of it's usage
        #
        # self.transaction = self.mocker.mock()
        # self.transactor = Transactor(self.threadpool, self.transaction)
        self.transactor = Transactor(self.threadpool)

        store = self.zstorm.create('testDB', 'sqlite:///test.db')
        store.execute(createQuery)
        store.commit()

    def tearDown(self):
        # Reset the utility to cleanup the StoreSynchronizer's from the
        # transaction.
        self.zstorm._reset()
        # Free the transaction to avoid having errors that cross
        # test cases.
        transaction.manager.free(transaction.get())
        # Remove the test database file
        os.remove('test.db')

    def getStore(self):
        return self.zstorm.get('testDB')

class TestTransactions(BaseZStormTestCase):

    @transact
    def test_addDummyModelWithTransactionMethod(self):
        store = self.getStore()
        d = DummyModel()
        store.add(d)

    @transact
    def test_addDummyModelAndFindIt(self):
        def addDummyModelTransaction():
            store = self.getStore()
            d = DummyModel()
            d.colInt = 42
            store.add(d)

        def findDummyModel():
            store = self.getStore()
            return store.find(DummyModel,
                DummyModel.colInt == 42).one()

        addDummyModelTransaction()
        dummyModel = findDummyModel()
        self.assertEqual(dummyModel.colInt, 42)

    @transact
    def test_addWrongModelRaises(self):
        def addDummyModelWithWrongValueTransaction():
            store = self.getStore()
            d = DummyModel()
            d.colInt = u'invalidValue'
            store.add(d)

        self.assertRaises(TypeError, addDummyModelWithWrongValueTransaction)

    @transact
    def test_findUnicodeInsteadOfIntRaises(self):
        def addDummyModel():
            store = self.getStore()
            d = DummyModel()
            d.colInt = 42
            store.add(d)

        def findWrongValueDummyModel():
            store = self.getStore()
            return store.find(DummyModel,
                DummyModel.colInt == u'invalidValue').one()

        addDummyModel()
        self.assertRaises(TypeError, findWrongValueDummyModel)

    @transact
    def test_findStrInsteadOfUnicodeRaises(self):
        def addDummyModel():
            store = self.getStore()
            d = DummyModel()
            d.colUnicode = u'spam'
            store.add(d)

        def findWrongValueDummyModel():
            store = self.getStore()
            return store.find(DummyModel,
                DummyModel.colUnicode == str('invalid')).one()

        addDummyModel()
        self.assertRaises(TypeError, findWrongValueDummyModel)

    @transact
    def test_findUnicode(self):
        def addDummyModel():
            store = self.getStore()
            d = DummyModel()
            d.colUnicode = u'spam'
            store.add(d)

        def findDummyModel():
            store = self.getStore()
            return store.find(DummyModel,
                DummyModel.colUnicode == unicode('spam')).one()

        addDummyModel()
        dummyModel = findDummyModel()
        self.assertEqual(dummyModel.colUnicode, u'spam')

    def test_multipleTransactions(self):
        def addDummyModel():
            store = self.getStore()
            d = DummyModel()
            d.colUnicode = u'spam'
            store.add(d)

        d1 = self.transactor.run(addDummyModel)
        d2 = self.transactor.run(addDummyModel)
        d3 = self.transactor.run(addDummyModel)
        d4 = self.transactor.run(addDummyModel)

        dl = defer.DeferredList([d1, d2, d3, d4])

        @dl.addCallback
        def finished(result):
            self.assertEqual(result[0], (True, None))
            self.assertEqual(result[1], (True, None))
            self.assertEqual(result[2], (True, None))
            self.assertEqual(result[3], (True, None))

        return dl

    def test_multipleTransactionsOneFailing(self):
        def addDummyModel():
            store = self.getStore()
            d = DummyModel()
            d.colUnicode = u'spam'
            store.add(d)

        def findWrongValueDummyModel():
            store = self.getStore()
            return store.find(DummyModel,
                DummyModel.colUnicode == str('invalid')).one()

        d1 = self.transactor.run(addDummyModel)

        d2 = self.transactor.run(findWrongValueDummyModel)
        @d2.addErrback
        def err(error):
            self.assertFailure(d2, TypeError)
            return error

        d3 = self.transactor.run(addDummyModel)
        d4 = self.transactor.run(addDummyModel)

        dl = defer.DeferredList([d1,d2, d3, d4])

        @dl.addCallback
        def finished(result):
            self.assertEqual(result[0], (True, None))

            self.assertEqual(result[1][0], False)

            self.assertEqual(result[2], (True, None))
            self.assertEqual(result[3], (True, None))

        return dl
