from twisted.internet import defer
from twisted.trial import unittest

from storm.twisted.testing import FakeThreadPool
from storm.twisted.transact import transact, Transactor

from storm.locals import *
from storm.databases.sqlite import SQLite
from storm.uri import URI

from globaleaks.db.models import TXModel
from globaleaks import db


class TestModels(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        threadpool = FakeThreadPool()
        self.transactor = Transactor(threadpool)
        self.database = SQLite(URI('sqlite:///test.db'))

        db.database = self.database
        db.threadpool = threadpool
        db.transactor = self.transactor

    @defer.inlineCallbacks
    def test_txmodel(self):

        class DummyModel(TXModel):
            transactor = self.transactor

            __storm_table__ = 'test'
            createQuery = "CREATE TABLE " + __storm_table__ +\
                          "(id INTEGER PRIMARY KEY, test INTEGER)"

            id = Int(primary=True)
            test = Int()

            @transact
            def find(self):
                store = db.getStore()
                res = store.find(DummyModel, DummyModel.test == 42).one()
                return res

        dm = DummyModel()
        yield dm.createTable()
        yield dm.save()

        dm = DummyModel()
        dm.test = 42
        yield dm.save()

        result = yield dm.find()
        self.assertEqual(result.test, 42)


