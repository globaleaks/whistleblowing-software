# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers import wizard
from globaleaks.rest import errors
from globaleaks.tests import helpers


class TestWizard(helpers.TestHandler):
    _handler = wizard.Wizard

    @inlineCallbacks
    def test_post(self):
        yield self.test_model_count(models.User, 0)

        handler = self.request(self.dummyWizard)
        yield handler.post()

        yield self.test_model_count(models.User, 2)

        # should fail if the wizard has been already completed
        handler = self.request(self.dummyWizard)
        yield self.assertFailure(handler.post(), errors.ForbiddenOperation)
