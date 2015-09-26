# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks.jobs import base

class TestGLJob(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_base_scheduler(self):
        yield base.GLJob()._operation()
