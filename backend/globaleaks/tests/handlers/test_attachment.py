# -*- coding: utf-8 -*-
import os

from globaleaks.handlers import attachment
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils import token
from twisted.internet.defer import inlineCallbacks


class TestSubmissionAttachment(helpers.TestHandlerWithPopulatedDB):
    _handler = attachment.SubmissionAttachment

    @inlineCallbacks
    def test_post_file_on_not_finalized_submission(self):
        self.dummyToken = token.Token(1, 'submission')
        self.dummyToken.proof_of_work = False

        handler = self.request()
        yield handler.post(self.dummyToken.id)

    @inlineCallbacks
    def test_post_file_and_verify_deletion_after_token_expiration(self):
        self.dummyToken = token.Token(1, 'submission')
        self.dummyToken.proof_of_work = False

        for _ in range(3):
            handler = self.request()
            yield handler.post(self.dummyToken.id)

        token.TokenList.reactor.pump([1] * (token.TokenList.get_timeout() - 1))

        for f in self.dummyToken.uploaded_files:
            self.assertTrue(os.path.exists(f['path']))

        token.TokenList.reactor.advance(1)

        for f in self.dummyToken.uploaded_files:
            yield self.assertFalse(os.path.exists(f['path']))

    @inlineCallbacks
    def test_post_file_on_unexistent_submission(self):
        handler = self.request()
        yield self.assertFailure(handler.post(u'unexistent_submission'), errors.TokenFailure)


class TestPostSubmissionAttachment(helpers.TestHandlerWithPopulatedDB):
    _handler = attachment.PostSubmissionAttachment

    @inlineCallbacks
    def test_post(self):
        yield self.perform_full_submission_actions()

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='whistleblower', user_id = wbtip_desc['id'])
            yield handler.post()
