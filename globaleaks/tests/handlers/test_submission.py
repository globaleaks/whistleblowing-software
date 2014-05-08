# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import node, submission
from globaleaks.settings import GLSetting
from globaleaks.security import GLSecureTemporaryFile

class Test_001_SubmissionCreate(helpers.TestHandler):
    _handler = submission.SubmissionCreate

    @inlineCallbacks
    def test_post(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False

        handler = self.request(submission_desc, {})
        yield handler.post()

        submission_desc = self.responses[0]

        self.responses = []

        yield self.emulate_file_upload(submission_desc['id'])

        submission_desc['finalize'] = True

        handler = self.request(submission_desc, {})
        yield handler.post()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)

class Test_002_SubmissionInstance(helpers.TestHandler):
    _handler = submission.SubmissionInstance

    def test_get_unexistent(self):
        handler = self.request({})
        self.assertFailure(handler.get("unextistent"), errors.SubmissionIdNotFound)

    def test_delete_unexistent(self):
        handler = self.request({})
        self.assertFailure(handler.delete("unextistent"), errors.SubmissionIdNotFound)
