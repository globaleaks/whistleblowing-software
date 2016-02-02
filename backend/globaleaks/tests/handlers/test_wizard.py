# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import wizard

class TestFirstSetup(helpers.TestHandler):
    _handler = wizard.FirstSetup

    @inlineCallbacks
    def test_post(self):
        # FIX currently wizard create contexts only with default fields
        # so only valid requests are the one with steps = []
        self.dummyContext['steps'] = []

        admin = {
          'old_password': 'globaleaks',
          'password': 'P4ssword', # <- hackingteam password! :)
          'mail_address': 'evilaliv3@globaleaks.org'
        }

        wizard_blob = {
            'node': self.dummyNode,
            'admin': admin,
            'receiver': self.get_dummy_receiver("christianice"),
            'context': self.dummyContext
        }

        handler = self.request(wizard_blob, role='admin')
        yield handler.post()
