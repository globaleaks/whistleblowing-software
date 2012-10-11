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

from globaleaks.db import createTables, threadpool
from globaleaks.db import transactor, getStore
from globaleaks.db.models import *

class DBTestCase(unittest.TestCase):

    def setUp(self):
        threadpool.start()

    def tearDown(self):
        threadpool.stop()

    @inlineCallbacks
    def test_add_tip(self):
        from datetime import datetime
        tip = InternalTip()
        yield tip.createTable()
        tip.fields = {'hello': 'world'}
        tip.comments = {'hello': 'world'}
        tip.pertinence = 0
        expiration_time = datetime.now()
        tip.expiration_time = expiration_time

        yield tip.save()

        def findtip(what):
            store = getStore()
            x = list(store.find(InternalTip, InternalTip.id == what))
            store.close()
            return x

        r_tip = yield transactor.run(findtip, tip.id)
        self.assertEqual(r_tip[0].fields['hello'], 'world')
        self.assertEqual(r_tip[0].comments['hello'], 'world')

    @inlineCallbacks
    def test_resume_submission(self):
        submission_id = '0000000000'
        submission = Submission()
        yield submission.createTable()

        submission.submission_id = unicode(submission_id)
        submission.folder_id = 0

        submission.fields = pickle.dumps({'fields': [{'hello': 'world'}]})

        submission.receivers = pickle.dumps({'receivers': [{'hello': 'world'}]})
        yield submission.save()

        resumed_submission = Submission()
        yield resumed_submission.resume(submission_id)



