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
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue

from storm.twisted.transact import Transactor
from storm.twisted.testing import FakeThreadPool, FakeTransactor
from storm.databases.sqlite import SQLite
from storm.uri import URI

from globaleaks.db import models

from globaleaks.messages.dummy import requests

class BaseDBTest(unittest.TestCase):
    def setUp(self):
        self.threadpool = FakeThreadPool()
        self.transactor = Transactor(self.threadpool)
        self.database = SQLite(URI("sqlite:///test.db"))

    def mock_model(self, model=None):
        if model:
            mock = model()
        else:
            mock = self.baseModel()
        mock.transactor = self.transactor
        mock.database = self.database
        return mock

    @inlineCallbacks
    def create_table(self, model=None):
        mock = self.mock_model(model)
        try:
            yield mock.createTable()
        except:
            pass

class TestSubmission(BaseDBTest):

    baseModel = models.Submission
    submission_id = u'r_testsubmissionid'

    @inlineCallbacks
    def test_create_table(self):
        yield self.create_table()

    @inlineCallbacks
    def create_dummy_submission(self, submission_id):
        test_submission = self.mock_model()
        test_submission.submission_id = submission_id
        test_submission.folder_id = 0

        test_submission.fields = requests.submissionStatusPost['fields']
        test_submission.receivers = requests.submissionStatusPost['receivers_selected']
        yield test_submission.save()

    @inlineCallbacks
    def test_submission_status(self):
        yield self.create_table()

        test_submission = self.mock_model()
        my_id = self.submission_id+'stat'

        yield self.create_dummy_submission(my_id)
        status = yield test_submission.status(my_id)

        self.assertEqual(status['fields'],
                requests.submissionStatusPost['fields'])
        self.assertEqual(status['receivers_selected'],
                requests.submissionStatusPost['receivers_selected'])

    @inlineCallbacks
    def test_finalize_submission(self):
        test_submission = self.mock_model()
        my_id = self.submission_id+'fina'

        yield self.create_table(models.InternalTip)
        yield self.create_table(models.Tip)

        yield self.create_dummy_submission(my_id)

        yield test_submission.create_tips(my_id, u'1234567890')

class TestTip(BaseDBTest):
    pass

class TestReceivers(BaseDBTest):
    pass
