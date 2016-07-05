# -*- encoding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.jobs import cleaning_sched
from globaleaks.utils.utility import datetime_null
from globaleaks.settings import GLSettings


class TestCleaningSched(helpers.TestGLWithPopulatedDB):
    @transact
    def force_itip_expiration(self, store):
        for tip in store.find(models.InternalTip):
            tip.expiration_date = datetime_null()

    @transact_ro
    def check0(self, store):
        self.assertTrue(os.listdir(GLSettings.submission_path) == [])
        self.assertTrue(os.listdir(GLSettings.tmp_upload_path) == [])

        self.assertEqual(store.find(models.InternalTip).count(), 0)
        self.assertEqual(store.find(models.ReceiverTip).count(), 0)
        self.assertEqual(store.find(models.InternalFile).count(), 0)
        self.assertEqual(store.find(models.ReceiverFile).count(), 0)
        self.assertEqual(store.find(models.Comment).count(), 0)
        self.assertEqual(store.find(models.Message).count(), 0)

    @transact_ro
    def check1(self, store):
        self.assertTrue(os.listdir(GLSettings.submission_path) != [])
        self.assertEqual(store.find(models.InternalTip).count(), 1)
        self.assertEqual(store.find(models.ReceiverTip).count(), 2)
        self.assertEqual(store.find(models.WhistleblowerTip).count(), 1)
        self.assertEqual(store.find(models.InternalFile).count(), 16)
        self.assertEqual(store.find(models.ReceiverFile).count(), 0)
        self.assertEqual(store.find(models.Comment).count(), 3)
        self.assertEqual(store.find(models.Message).count(), 4)

    @inlineCallbacks
    def test_submission_life(self):
        # verify that the system starts clean
        yield self.check0()

        yield self.perform_full_submission_actions()
        # verify tip creation
        yield self.check1()

        yield cleaning_sched.CleaningSchedule().operation()

        # verify tip survive the scheduler if they are not expired
        yield self.check1()

        yield self.force_itip_expiration()

        yield cleaning_sched.CleaningSchedule().operation()

        # verify cascade deletion when tips expire
        yield self.check0()
