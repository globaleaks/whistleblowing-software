# -*- coding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.handlers import files
from globaleaks.utils import token

class TestFileInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = files.FileInstance

    @inlineCallbacks
    def test_post_file_on_not_finalized_submission(self):
        self.dummyToken = token.Token(token_kind='submission',
                                      context_id=self.dummyContext['id'])

        handler = self.request(body=self.get_dummy_file())
        yield handler.post(self.dummyToken.token_id)

    @inlineCallbacks
    def test_post_file_and_verify_deletion_after_token_expiration(self):
        self.dummyToken = token.Token(token_kind='submission',
                                      context_id=self.dummyContext['id'])

        for i in range(0, 3):
            handler = self.request(body=self.get_dummy_file())
            yield handler.post(self.dummyToken.token_id)

        for f in self.dummyToken.uploaded_files:
            self.assertTrue(os.path.exists(f['encrypted_path']))

        token.reactor_override.advance(360000) # advance clock of 100 hours

        for f in self.dummyToken.uploaded_files:
            self.assertFalse(os.path.exists(f['encrypted_path']))

    @inlineCallbacks
    def test_post_file_finalized_submission(self):
        yield self.perform_full_submission_actions()
        handler = self.request(body=self.get_dummy_file())
        self.assertFailure(handler.post(self.dummySubmission['id']), errors.TokenFailure)

    def test_post_file_on_unexistent_submission(self):
        handler = self.request(body=self.get_dummy_file())
        self.assertFailure(handler.post(u'unexistent_submission'), errors.TokenFailure)

class TestFileAdd(helpers.TestHandlerWithPopulatedDB):
    _handler = files.FileAdd

    @inlineCallbacks
    def test_post(self):
        yield self.perform_full_submission_actions()

        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb', body=self.get_dummy_file())
            handler.current_user.user_id = wbtip_desc['wbtip_id']
            yield handler.post()

class TestDownload(helpers.TestHandlerWithPopulatedDB):
    _handler = files.Download

    @inlineCallbacks
    def test_post(self):
        yield self.perform_full_submission_actions()

        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            rfiles_desc = yield self.get_rfiles(rtip_desc['rtip_id'])
            for rfile_desc in rfiles_desc:
                handler = self.request(role='receiver')
                handler.current_user.user_id = rtip_desc['receiver_id']
                yield handler.post(rtip_desc['rtip_id'], rfile_desc['rfile_id'])
