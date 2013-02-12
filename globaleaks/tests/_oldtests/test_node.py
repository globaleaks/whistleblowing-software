# test_node.py
from twisted.trial import unittest
import os
import transaction
from storm.twisted.testing import FakeThreadPool
from storm.twisted.transact import Transactor
from storm.info import get_cls_info
from twisted.internet import defer

from globaleaks import main
from globaleaks.settings import config, get_db_file
from globaleaks.db import tables, initializeNode
from globaleaks.models.node import Node

class NodeTest(unittest.TestCase):
    def setUp(self):
        self.threadpool = FakeThreadPool()
        self.transactor = Transactor(self.threadpool)
        main.transactor = self.transactor

        config.__init__(get_db_file('test.db'))

        # this call is to create the db file: test.db
        # the file is than removed in teardown using os.remove()
        config.main.zstorm.get('main_store')

    def tearDown(self):
        # Free the transaction to avoid having errors that cross
        # test cases.
        # Remove the test database file
        os.remove(get_db_file('test.db'))

    def test_01_create_cable(self):
        @defer.inlineCallbacks
        def run_test():
            yield tables.runCreateTable(Node)

        return run_test()

    def test_02_test_empy_table(self):
        @defer.inlineCallbacks
        def run_test():
            yield tables.runCreateTable(Node)

            count = tables.count(Node)
            self.assertEqual(count, 0)

        return run_test()

    def test_03_insert_and_get(self):
        @defer.inlineCallbacks
        def run_test():
            yield tables.runCreateTable(Node)

            count = tables.count(Node)
            self.assertEqual(count, 0)

            store = config.main.zstorm.get('main_store')
            nodetest = Node()
            nodetest.name = u"test"
            nodetest.description = u"test"
            nodetest.hidden_service = u"test"
            nodetest.public_site = u"test"
            nodetest.email = u"email@dummy.net"
            nodetest.private_stats_update_time = 30 # minutes
            nodetest.public_stats_update_time = 120 # minutes
            nodetest.languages = [ { "code" : "it" , "name": "Italiano"}, { "code" : "en" , "name" : "English" }]
            store.add(nodetest)

            count = tables.count(Node)
            self.assertEqual(count, 1)

            # select & verify
            node = store.find(Node, 1 == Node.id).one()
            cls_info = get_cls_info(Node)
            for name in cls_info.attributes.iterkeys():
                self.assertEqual(getattr(node, name, ""), getattr(nodetest, name, ""))

        return run_test()
