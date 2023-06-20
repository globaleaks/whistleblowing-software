# -*- coding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs import cleaning, delivery
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.tests import helpers


class TestCleaning(helpers.TestGLWithPopulatedDB):
    @transact
    def check0(self, session):
        self.assertEqual(len(os.listdir(Settings.attachments_path)), 0)
        self.assertEqual(len(os.listdir(Settings.tmp_path)), 0)

        self.db_test_model_count(session, models.InternalTip, 0)
        self.db_test_model_count(session, models.ReceiverTip, 0)
        self.db_test_model_count(session, models.InternalFile, 0)
        self.db_test_model_count(session, models.ReceiverFile, 0)
        self.db_test_model_count(session, models.Comment, 0)
        self.db_test_model_count(session, models.Mail, 0)

    @transact
    def check1(self, session):
        self.assertEqual(len(os.listdir(Settings.attachments_path)), self.population_of_submissions * self.population_of_attachments)

        self.db_test_model_count(session, models.InternalTip, self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverTip, self.population_of_recipients * self.population_of_submissions)
        self.db_test_model_count(session, models.InternalFile, self.population_of_submissions * self.population_of_attachments)
        self.db_test_model_count(session, models.ReceiverFile, self.population_of_submissions * self.population_of_attachments * self.population_of_recipients)
        self.db_test_model_count(session, models.Comment, self.population_of_submissions * (self.population_of_recipients + 1))
        self.db_test_model_count(session, models.Mail, 0)

    @transact
    def check2(self, session):
        self.assertEqual(len(os.listdir(Settings.attachments_path)), self.population_of_submissions * self.population_of_attachments)

        self.db_test_model_count(session, models.InternalTip, self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverTip, self.population_of_recipients * self.population_of_submissions)
        self.db_test_model_count(session, models.InternalFile, self.population_of_submissions * self.population_of_attachments)
        self.db_test_model_count(session, models.ReceiverFile, self.population_of_submissions * self.population_of_attachments * self.population_of_recipients)
        self.db_test_model_count(session, models.Comment, self.population_of_submissions * (self.population_of_recipients + 1))
        self.db_test_model_count(session, models.Mail, 0)

    @transact
    def check3(self, session):
        self.assertEqual(len(os.listdir(Settings.attachments_path)), self.population_of_submissions * self.population_of_attachments)

        self.db_test_model_count(session, models.InternalTip, self.population_of_submissions)
        self.db_test_model_count(session, models.ReceiverTip, self.population_of_recipients * self.population_of_submissions)
        self.db_test_model_count(session, models.InternalFile, self.population_of_submissions * self.population_of_attachments)
        self.db_test_model_count(session, models.ReceiverFile, self.population_of_submissions * self.population_of_attachments * self.population_of_recipients)
        self.db_test_model_count(session, models.Comment, self.population_of_submissions * (self.population_of_recipients + 1))
        self.db_test_model_count(session, models.Mail, self.population_of_recipients)

    @transact
    def check4(self, session):
        self.assertEqual(len(os.listdir(Settings.attachments_path)), 0)

        self.db_test_model_count(session, models.InternalTip, 0)
        self.db_test_model_count(session, models.ReceiverTip, 0)
        self.db_test_model_count(session, models.InternalFile, 0)
        self.db_test_model_count(session, models.ReceiverFile, 0)
        self.db_test_model_count(session, models.Comment, 0)
        self.db_test_model_count(session, models.Mail, self.population_of_recipients)

    @inlineCallbacks
    def test_job(self):
        # verify that the system starts clean
        yield self.check0()

        yield self.perform_full_submission_actions()

        yield delivery.Delivery().run()

        # verify tip creation
        yield self.check1()

        # mark files as uploaded on timestamp 0
        for f in os.listdir(Settings.attachments_path):
            path = os.path.join(Settings.attachments_path, f)
            os.utime(path, (0, 0))

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
