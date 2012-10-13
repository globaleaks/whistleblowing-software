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

from globaleaks.db import base

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

    baseModel = base.Submission
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

        yield self.create_table(base.InternalTip)
        yield self.create_table(base.Tip)

        yield self.create_dummy_submission(my_id)

        yield test_submission.create_tips(my_id, u'1234567890')

class TestReceivers(BaseDBTest):
    baseModel = base.Receiver

    @inlineCallbacks
    def create_tables(self):
        yield self.create_table(base.Receiver)
        yield self.create_table(base.ReceiverContext)
        yield self.create_table(base.Context)

    @inlineCallbacks
    def test_create_tables(self):
        yield self.create_tables()

    @inlineCallbacks
    def test_create_dummy_receivers(self):
        test_receiver = self.mock_model()
        yield self.create_table()
        result = yield test_receiver.create_dummy_receivers()
        receiver_dict = yield test_receiver.receiver_dicts()

        # XXX by doing this test in this way we are assuming ordering on the
        # receiver dict table. This assumption may be wrong.
        self.assertEqual(result[0], receiver_dict[0])

    @inlineCallbacks
    def test_add_receiver_to_context(self):
        context_id = u'c_thisisatestcontext'
        test_receiver = self.mock_model()
        test_context = self.mock_model(base.Context)
        test_context.name = u'test context'
        test_context.context_id = context_id

        yield self.create_tables()
        yield test_context.save()

        result = yield test_receiver.create_dummy_receivers()

        receiver_id = result[0]['receiver_id']
        yield test_context.add_receiver(context_id, receiver_id)


class TestTip(BaseDBTest):
    pass


