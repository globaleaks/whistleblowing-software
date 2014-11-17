# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSetting
from globaleaks.tests import helpers
from globaleaks.handlers import wizard
from globaleaks.db.datainit import opportunistic_appdata_init

class TestWizardCollection(helpers.TestHandler):
    _handler = wizard.AppdataCollection

    @inlineCallbacks
    def test_post(self):

        appdata_blob = opportunistic_appdata_init()

        handler = self.request(appdata_blob, role='admin')
        yield handler.post()

        appdata_blob['version'] = (appdata_blob['version'] + 1)

        handler = self.request(appdata_blob, role='admin')
        yield handler.post()

        yield handler.get()
        self.assertEqual(len(self.responses[2]), len(appdata_blob['fields']) )
        self.assertEqual(self.responses[2]['version'], appdata_blob['version'])


class TestFirstSetup(helpers.TestHandler):
    _handler = wizard.FirstSetup

    @inlineCallbacks
    def test_post(self):

        appdata_blob = opportunistic_appdata_init()

        # FIX currently wizard create contexts only with default fields
        # so only valid requests are the one with steps = []
        self.dummyContext['steps'] = []

        wizard_blob = {
            'receiver' : self.get_dummy_receiver("christianice"),
            'fields' : self.dummyFields,
            'context' : self.dummyContext,
            'node' : self.dummyNode,
            'appdata' : appdata_blob,
        }

        handler = self.request(wizard_blob, role='admin')
        yield handler.post()
