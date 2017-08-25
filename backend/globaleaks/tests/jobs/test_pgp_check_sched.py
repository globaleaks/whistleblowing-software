# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.jobs import pgp_check_sched
from globaleaks.orm import transact
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestPGPCheckSchedule(helpers.TestGLWithPopulatedDB):
    encryption_scenario = 'ENCRYPTED_WITH_ONE_KEY_EXPIRED'

    @transact
    def assert_expired_or_expiring_pgp_users_count(self, store, count):
        return self.assertEqual(pgp_check_sched.db_get_expired_or_expiring_pgp_users(store).count(), count)

    @inlineCallbacks
    def test_pgp_check_schedule(self):
        yield self.test_model_count(models.Mail, 0)

        yield self.assert_expired_or_expiring_pgp_users_count(1)

        yield pgp_check_sched.PGPCheckSchedule().run()

        yield self.test_model_count(models.Mail, 2)

        yield self.assert_expired_or_expiring_pgp_users_count(0)
