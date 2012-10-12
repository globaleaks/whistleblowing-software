import json
import sys
import os
import pickle
print __file__
# hack to add globaleaks to the sys path
cwd = '/'.join(__file__.split('/')[:-1])
sys.path.insert(0, os.path.join(cwd, '../../'))

from twisted.python import log
from twisted.trial import unittest
from twisted.internet import reactor
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.internet.protocol import Protocol
from twisted.internet.defer import Deferred, inlineCallbacks

from storm.twisted.transact import Transactor
from storm.twisted.testing import FakeThreadPool, FakeTransactor
from storm.databases.sqlite import SQLite
from storm.uri import URI

from globaleaks.db import models

class BaseDBTest(unittest.TestCase):
    def setUp(self):
        fake_thread_pool = FakeThreadPool()
        self.transactor = Transactor(fake_thread_pool)
        self.database = SQLite(URI("sqlite:///test.db"))

    def mock_model(self):
        mock = self.baseModel()
        mock.transactor = self.transactor
        mock.database = self.database
        return mock

    @inlineCallbacks
    def create_table(self):
        mock = self.mock_model()
        try:
            yield mock.createTable()
        except:
            pass

class TestSubmission(BaseDBTest):
    baseModel = models.Submission

    @inlineCallbacks
    def test_create_table(self):
        yield self.create_table()

    @inlineCallbacks
    def test_new_submission(self):
        from globaleaks.utils import idops
        from globaleaks.messages.dummy import requests
        yield self.create_table()

        test_id = unicode(idops.random_submission_id())
        test_submission = self.mock_model()
        test_submission.submission_id = test_id
        test_submission.folder_id = 0

        test_submission.fields = requests.submissionStatusPost['fields']
        test_submission.receivers = requests.submissionStatusPost['receivers_selected']
        yield test_submission.save()

        status = yield test_submission.status(test_id)
        self.assertEqual(status['fields'],
                requests.submissionStatusPost['fields'])
        self.assertEqual(status['receivers_selected'],
                requests.submissionStatusPost['receivers_selected'])

class TestTip(BaseDBTest):
    pass


class TestReceivers(BaseDBTest):
    pass
