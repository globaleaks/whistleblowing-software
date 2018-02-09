# -*- coding: utf-8 -*-
import os

from globaleaks import models
from globaleaks.jobs import cleaning, delivery
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.tests import helpers
from twisted.internet.defer import inlineCallbacks


class TestCleaning(helpers.TestGLWithPopulatedDB):
    @transact
    def check0(self, session):
        self.assertTrue(os.listdir(Settings.attachments_path) == [])
        self.assertTrue(os.listdir(Settings.tmp_path) == [])

        self.db_test_model_count(session, models.InternalTip, 0)
        self.db_test_model_count(session, models.ReceiverTip, 0)
        self.db_test_model_count(session, models.InternalFile, 0)
        self.db_test_model_count(session, models.ReceiverFile, 0)
        self.db_test_model_count(session, models.Comment, 0)
        self.db_test_model_count(session, models.Message, 0)
        self.db_test_model_count(session, models.Mail, 0)
        self.db_test_model_count(session, models.SecureFileDelete, 0)

    @transact
    def check1(self, session):
        self.assertTrue(os.listdir(Settings.attachments_path) != [])

        self.db_test_model_count(session, models.InternalTip, self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverTip, self.population_of_recipients * self.population_of_submissions)
        self.db_test_model_count(session, models.InternalFile, self.population_of_attachments * self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverFile, self.population_of_attachments * self.population_of_submissions * self.population_of_recipients)
        self.db_test_model_count(session, models.Comment, self.population_of_submissions * (self.population_of_recipients + 1))
        self.db_test_model_count(session, models.Message, self.population_of_submissions * (self.population_of_recipients + 2))
        self.db_test_model_count(session, models.Mail, 0)
        self.db_test_model_count(session, models.SecureFileDelete, 0)

    @transact
    def check2(self, session):
        self.assertTrue(os.listdir(Settings.attachments_path) != [])

        self.db_test_model_count(session, models.InternalTip, self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverTip, self.population_of_recipients * self.population_of_submissions)
        self.db_test_model_count(session, models.InternalFile, self.population_of_attachments * self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverFile, self.population_of_attachments * self.population_of_submissions * self.population_of_recipients)
        self.db_test_model_count(session, models.Comment, self.population_of_submissions * (self.population_of_recipients + 1))
        self.db_test_model_count(session, models.Message, self.population_of_submissions * (self.population_of_recipients + 2))
        self.db_test_model_count(session, models.Mail, 0)
        self.db_test_model_count(session, models.SecureFileDelete, 0)

    @transact
    def check3(self, session):
        self.assertTrue(os.listdir(Settings.attachments_path) != [])

        self.db_test_model_count(session, models.InternalTip, self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverTip, self.population_of_recipients * self.population_of_submissions)
        self.db_test_model_count(session, models.InternalFile, self.population_of_attachments * self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverFile, self.population_of_attachments * self.population_of_submissions * self.population_of_recipients)
        self.db_test_model_count(session, models.Comment, self.population_of_submissions * (self.population_of_recipients + 1))
        self.db_test_model_count(session, models.Message, self.population_of_submissions * (self.population_of_recipients + 2))
        self.db_test_model_count(session, models.Mail, self.population_of_recipients)
        self.db_test_model_count(session, models.SecureFileDelete, 0)

    @transact
    def check4(self, session):
        self.assertTrue(os.listdir(Settings.attachments_path) == [])
        self.assertTrue(os.listdir(Settings.tmp_path) == [])

        self.db_test_model_count(session, models.InternalTip, 0)
        self.db_test_model_count(session, models.ReceiverTip, 0)
        self.db_test_model_count(session, models.InternalFile, 0)
        self.db_test_model_count(session, models.ReceiverFile, 0)
        self.db_test_model_count(session, models.Comment, 0)
        self.db_test_model_count(session, models.Message, 0)
        self.db_test_model_count(session, models.Mail, self.population_of_recipients)
        self.db_test_model_count(session, models.SecureFileDelete, 0)

    @inlineCallbacks
    def test_submission_life(self):
        # verify that the system starts clean
        yield self.check0()

        yield self.perform_full_submission_actions()

        yield delivery.Delivery().run()

        # verify tip creation
        yield self.check1()

        yield cleaning.Cleaning().run()

        # verify tips survive the scheduler if they are not expired
        yield self.check1()

        yield self.force_wbtip_expiration()

        yield cleaning.Cleaning().run()

        # verify rtips survive the scheduler if the wbtip expires
        yield self.check2()

        yield self.set_itips_near_to_expire()

        yield cleaning.Cleaning().run()

        # verify mail creation and that rtips survive the scheduler
        yield self.check3()

        yield self.force_itip_expiration()

        yield cleaning.Cleaning().run()

        # verify cascade deletion when tips expire
        yield self.check4()
