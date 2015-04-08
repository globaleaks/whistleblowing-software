# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks.jobs import pgp_check_sched

class TestPGPCheckSchedule(helpers.TestGLWithPopulatedDB):

    encryption_scenario = 'ONE_VALID_ONE_EXPIRED'

    @inlineCallbacks
    def test_pgp_check_schedule(self):

        # FIXME: complete this unit test by performing checks
        #        on the actions performed by the scheduler.
        yield pgp_check_sched.PGPCheckSchedule().operation()

