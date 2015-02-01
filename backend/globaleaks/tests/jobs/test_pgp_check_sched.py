# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.settings import GLSetting, transact, transact_ro
from globaleaks.models import Receiver

from globaleaks.jobs import pgp_check_sched

class TestPGPCheckSchedule(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def test_pgp_check_schedule(self):
        # FIXME: complete this unit test by performing checks
        #        on the actions performed by the scheduler.
        yield pgp_check_sched.PGPCheckSchedule().operation()

