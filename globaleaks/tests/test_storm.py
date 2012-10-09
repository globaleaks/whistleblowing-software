from twisted.internet import defer
from twisted.trial import unittest

from storm.twisted.testing import FakeThreadPool
from storm.twisted.transact import transact, Transactor

from storm.locals import *
from storm.databases.sqlite import SQLite
from storm.uri import URI

from globaleaks.db.models import TXModel

createQuery = "CREATE TABLE test"\
              "(id INTEGER PRIMARY KEY, test INTEGER)"


class TestModels(unittest.TestCase):
    created = False

    def setUp(self):
        unittest.TestCase.setUp(self)

        #database = SQLite(URI('sqlite:'))

        threadpool = FakeThreadPool()
        self.transactor = Transactor(threadpool)

        database = create_database("sqlite:///test.db")
        c_store = Store(database)
        try:
            c_store.execute(createQuery)
            c_store.commit()
        except:
            print "Already exists!"

        def getStore():
            store = Store(database)
            return store

        class DummyModel(TXModel):
            transactor = self.transactor
            __storm_table__ = 'test'

            id = Int(primary=True)
            test = Int()

            @transact
            def save(self):
                store = getStore()
                store.add(self)
                store.commit()

            @transact
            def find(self):
                store = getStore()
                res = store.find(DummyModel, DummyModel.test == 42).one()
                store.close()
                return res

            @transact
            def find_more(self):
                output = []
                store = getStore()
                res = store.find(DummyModel, DummyModel.test > 2)
                for x in res:
                    output.append(x)
                store.close()
                return output

        self.DM = DummyModel

    @defer.inlineCallbacks
    def test_txmodel(self):
        dm = self.DM()
        dm.test = 42
        yield dm.save()

        result = yield dm.find()
        #self.assertEqual(result.test, 42)

    @defer.inlineCallbacks
    def test_find_more(self):

        for x in range(10):
            dm = self.DM()
            dm.test = x
            yield dm.save()

        result = yield dm.find_more()

        i = 3
        for r in result:
            self.assertEqual(r.test, i)
            i += 1

