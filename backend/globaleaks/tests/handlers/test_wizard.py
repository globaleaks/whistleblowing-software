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

        wizard_blob = {
            'receiver' : self.get_dummy_receiver("christianice"),
            'fields' : self.dummyFields,
            'context' : self.dummyContext,
            'node' : self.dummyNode,
        }

        handler = self.request(wizard_blob, role='admin')
        yield handler.post()
