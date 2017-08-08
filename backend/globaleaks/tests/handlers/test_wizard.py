# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import wizard
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.settings import GLSettings
from globaleaks.orm import transact


class TestWizard(helpers.TestHandler):
    _handler = wizard.Wizard

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandler.setUp(self)

        # FIX currently wizard create contexts only with default fields
        # so only valid requests are the one with steps = []
        self.dummyContext['steps'] = []

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
        self.dummyContext['steps'] = []

        handler = self.request(self.wizard_blob)
        yield handler.post()

        handler = self.request(self.wizard_blob)
        yield self.assertFailure(handler.post(), errors.ForbiddenOperation)


class TestProfileLoad(helpers.TestHandler):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandler.setUp(self)
        self.old_path = GLSettings.client_path
        GLSettings.client_path = os.path('..', helpers.DATA_DIR)

    @inlineCallbacks
    def test_invalid_load(self):
        t = transact(load_profile)

        self.assertFailure(errors.ValidationError, t, 'invalid')

    @inlineCallbacks
    def tearDown(self):
        GLSettings.client_path = self.old_path
        yield helpers.TestHandler.tearDown(self)
