# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import files
from globaleaks.settings import GLSetting
from globaleaks.security import GLSecureTemporaryFile

class TestFileInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = files.FileInstance

    @inlineCallbacks
    def test_001_post_file_on_not_finalized_submission(self):
        handler = self.request(body=self.get_dummy_file())
        yield handler.post(self.dummySubmissionNotFinalized['id'])

    def test_002_post_file_finalized_submission(self):
        handler = self.request(body=self.get_dummy_file())
        self.assertFailure(handler.post(self.dummySubmission['id']), errors.SubmissionConcluded)

    def test_003_post_file_on_unexistent_submission(self):
        handler = self.request(body=self.get_dummy_file())
        self.assertFailure(handler.post(u'unexistent_submission'), errors.SubmissionIdNotFound)

class TestFileAdd(helpers.TestHandlerWithPopulatedDB):
    _handler = files.FileAdd

    @inlineCallbacks
    def test_001_post(self):
        wbtips_desc = yield self.get_wbtips()
        for wbtip_desc in wbtips_desc:
            handler = self.request(role='wb', body=self.get_dummy_file())
            handler.current_user.user_id = wbtip_desc['wbtip_id']
            yield handler.post()

class TestDownload(helpers.TestHandlerWithPopulatedDB):
    _handler = files.Download

    @inlineCallbacks
    def test_001_post(self):
        rtips_desc = yield self.get_rtips()
        for rtip_desc in rtips_desc:
            rfiles_desc = yield self.get_rfiles(rtip_desc['rtip_id'])
            for rfile_desc in rfiles_desc:
                handler = self.request(role='receiver')
                handler.current_user.user_id = rtip_desc['receiver_id']
                yield handler.post(rtip_desc['rtip_id'], rfile_desc['rfile_id'])
