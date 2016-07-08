# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import wizard
from globaleaks.rest import errors
from globaleaks.security import generateRandomSalt, derive_auth_hash
from globaleaks.tests import helpers


class TestWizard(helpers.TestHandler):
    _handler = wizard.Wizard

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandler.setUp(self)

        # FIX currently wizard create contexts only with default fields
        # so only valid requests are the one with steps = []
        self.dummyContext['steps'] = []

        salt = 'salt!'

        admin = {
            'salt': generateRandomSalt(),
            'auth': {
                'old_auth_token_hash': derive_auth_hash('password', salt),
                'new_auth_token_hash': derive_auth_hash('password', salt),
                'ccrypto_key_public': '',
                'ccrypto_key_private': ''
             },
            'mail_address': 'evilaliv3@globaleaks.org',
        }

        self.wizard_blob = {
            'node': self.dummyNode,
            'admin': admin,
            'receiver': self.get_dummy_receiver("christianice"),
            'context': self.dummyContext
        }

    @inlineCallbacks
    def test_post(self):
        handler = self.request(self.wizard_blob, role='admin')
        yield handler.post()

    @inlineCallbacks
    def test_fail_after_first_post(self):
        self.dummyContext['steps'] = []

        handler = self.request(self.wizard_blob, role='admin')
        yield handler.post()

        handler = self.request(self.wizard_blob, role='admin')
        yield self.assertFailure(handler.post(), errors.ForbiddenOperation)
