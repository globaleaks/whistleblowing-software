# -*- coding: utf-8 -*-
import os

from globaleaks.handlers import wizard
from globaleaks.models.profiles import load_profile
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestWizard(helpers.TestHandler):
    _handler = wizard.Wizard

    @inlineCallbacks
    def test_post(self):
        handler = self.request(self.dummyWizard)
        yield handler.post()

    @inlineCallbacks
    def test_fail_after_first_post(self):
        handler = self.request(self.dummyWizard)
        yield handler.post()

        handler = self.request(self.dummyWizard)
        yield self.assertFailure(handler.post(), errors.ForbiddenOperation)


class TestProfileLoad(helpers.TestHandler):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandler.setUp(self)
        self.old_path = Settings.client_path
        Settings.client_path = os.path.join(helpers.DATA_DIR, '..')

    @inlineCallbacks
    def test_invalid_load(self):
        yield self.assertFailure(transact(load_profile)(1, 'invalid'), ValueError)
        yield self.assertFailure(transact(load_profile)(1, 'default'), ValueError)

    @inlineCallbacks
    def tearDown(self):
        Settings.client_path = self.old_path
        yield helpers.TestHandler.tearDown(self)
