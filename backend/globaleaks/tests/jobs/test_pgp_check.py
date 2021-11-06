# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.jobs import pgp_check
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestPGPCheckWithNoKeys(helpers.TestGLWithPopulatedDB):
    pgp_configuration = 'NONE'

    @inlineCallbacks
    def test_pgp_checkule(self):
        yield self.test_model_count(models.Mail, 0)

        yield pgp_check.PGPCheck().run()

        yield self.test_model_count(models.Mail, 0)


class TestPGPCheckWithValidKeys(helpers.TestGLWithPopulatedDB):
    pgp_configuration = 'ALL'

    @inlineCallbacks
    def test_pgp_checkule(self):
        yield self.test_model_count(models.Mail, 0)

        yield pgp_check.PGPCheck().run()

        yield self.test_model_count(models.Mail, 0)


class TestPGPCheckWithExpiredKey(helpers.TestGLWithPopulatedDB):
    pgp_configuration = 'ONE_VALID_ONE_EXPIRED'

    @inlineCallbacks
    def test_pgp_checkule(self):
        yield self.test_model_count(models.Mail, 0)

        yield pgp_check.PGPCheck().run()

        yield self.test_model_count(models.Mail, 2)
