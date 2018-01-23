# -*- coding: utf-8 -*-
from globaleaks.handlers import wizard
from globaleaks.rest import errors
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestWizard(helpers.TestHandler):
    _handler = wizard.Wizard

    @inlineCallbacks
    def test_post(self):
        handler = self.request(self.dummyWizard)
        yield handler.post()

        # should fail if the wizard has been already completed
        handler = self.request(self.dummyWizard)
        yield self.assertFailure(handler.post(), errors.ForbiddenOperation)
