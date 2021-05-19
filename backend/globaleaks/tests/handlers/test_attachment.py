# -*- coding: utf-8 -*-
import os

from globaleaks.handlers import attachment, submission
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestSubmissionAttachment(helpers.TestHandlerWithPopulatedDB):
    _handler = attachment.SubmissionAttachment

    def test_post_file_on_not_finalized_submission(self):
        self.dummyToken = self.state.tokens.new(1)
        self.dummyToken.solved = True

        handler = self.request()

        return handler.post(self.dummyToken.id)

    @inlineCallbacks
    def test_post_file_and_verify_deletion_after_submission_expiration(self):
        submission_id = submission.initialize_submission()['id']

        for _ in range(3):
            handler = self.request()
            yield handler.post(submission_id)

        self.state.tokens.reactor.pump([1] * (self.state.tokens.timeout - 1))

        for f in self.state.TempSubmissions[submission_id].files:
            path = os.path.abspath(os.path.join(self.state.settings.tmp_path, f['filename']))
            self.assertTrue(os.path.exists(path))

        self.state.tokens.reactor.advance(1)

        for f in self.state.TempSubmissions[submission_id].files:
            path = os.path.abspath(os.path.join(self.state.settings.attachments_path, f['filename']))
            yield self.assertFalse(os.path.exists(path))

    def test_post_file_on_unexistent_submission(self):
        handler = self.request()
        self.assertIsNone(handler.post('unexistent_submission'))


class TestPostSubmissionAttachment(helpers.TestHandlerWithPopulatedDB):
    _handler = attachment.PostSubmissionAttachment

    @inlineCallbacks
    def test_post(self):
        yield self.perform_full_submission_actions()

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='whistleblower', user_id=wbtip_desc['id'])
            yield handler.post()
