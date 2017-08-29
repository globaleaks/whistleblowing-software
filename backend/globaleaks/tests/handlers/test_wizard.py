# -*- coding: utf-8 -*-
import os

from globaleaks.handlers import wizard
from globaleaks.models.profiles import load_profile
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestWizard(helpers.TestHandler):
    _handler = wizard.Wizard

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandler.setUp(self)

        admin = {
            'old_password': 'globaleaks',
            'password': 'P4ssword',  # <- hackingteam password! :)
            'mail_address': 'evilaliv3@globaleaks.org'
        }

        self.wizard_blob = {
            'node': self.dummyNode,
            'admin': admin,
            'receiver': self.get_dummy_receiver("christisnice"),
            'context': self.dummyContext,
            'profile': 'default',
        }

    @inlineCallbacks
    def test_post(self):
        handler = self.request(self.wizard_blob)
        yield handler.post()

    @inlineCallbacks
    def test_fail_after_first_post(self):
        handler = self.request(self.wizard_blob)
        yield handler.post()

        handler = self.request(self.wizard_blob)
        yield self.assertFailure(handler.post(), errors.ForbiddenOperation)


class TestProfileLoad(helpers.TestHandler):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandler.setUp(self)
        self.old_path = GLSettings.client_path
        GLSettings.client_path = os.path.join(helpers.DATA_DIR, '..')

    @inlineCallbacks
    def test_invalid_load(self):
        yield self.assertFailure(transact(load_profile)('invalid'), ValueError)
        yield self.assertFailure(transact(load_profile)('default'), ValueError)

    @inlineCallbacks
    def tearDown(self):
        GLSettings.client_path = self.old_path
        yield helpers.TestHandler.tearDown(self)
