# -*- encoding: utf-8 -*-
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks import models
from globaleaks.handlers import admin, rtip, receiver
from globaleaks.jobs import cleaning_sched
from globaleaks.utils.utility import is_expired, datetime_null
from globaleaks.settings import transact, GLSetting


class TestCleaning(helpers.TestGLWithPopulatedDB):
    @transact
    def test_postpone_survive_cleaning(self, store):
        self.assertEqual(store.find(models.InternalTip).count(), 1)
        self.assertEqual(store.find(models.ReceiverTip).count(), 2)
        self.assertEqual(store.find(models.WhistleblowerTip).count(), 1)

    @transact
    def test_cleaning(self, store):
        self.assertEqual(store.find(models.InternalTip).count(), 0)
        self.assertEqual(store.find(models.ReceiverTip).count(), 0)
        self.assertEqual(store.find(models.WhistleblowerTip).count(), 0)
        self.assertEqual(store.find(models.InternalFile).count(), 0)
        self.assertEqual(store.find(models.ReceiverFile).count(), 0)
        self.assertEqual(store.find(models.Comment).count(), 0)

    @transact
    def check_tip_not_expired(self, store):
        tips = store.find(models.InternalTip)
        for tip in tips:
            self.assertFalse(is_expired(tip.expiration_date))

    @transact
    def force_tip_expire(self, store):
        tips = store.find(models.InternalTip)
        for tip in tips:
            tip.expiration_date = datetime_null()

    # -------------------------------------------
    # Those the two class implements the sequence
    # -------------------------------------------

class TipCleaning(TestCleaning):

    @inlineCallbacks
    def postpone_tip_expiration(self):
        recv_desc = yield admin.get_receiver_list('en')
        self.assertEqual(len(recv_desc), 2)
        rtip_desc = yield receiver.get_receivertip_list(recv_desc[0]['id'], 'en')
        self.assertEqual(len(rtip_desc), 1)
        rtip.postpone_expiration_date(recv_desc[0]['id'], rtip_desc[0]['id'])

        yield cleaning_sched.CleaningSchedule().operation()

    @inlineCallbacks
    def test_unfinished_submission_life_and_expire(self):
        yield self.perform_submission_start()
        yield self.perform_submission_uploads()

    @inlineCallbacks
    def test_tip_life_and_expire(self):
        yield self.perform_full_submission_actions()
        yield self.check_tip_not_expired()

        yield self.force_tip_expire()

        yield cleaning_sched.CleaningSchedule().operation()

        yield self.test_cleaning()

    @inlineCallbacks
    def test_tip_life_postpone(self):
        yield self.perform_full_submission_actions()
        yield self.check_tip_not_expired()

        yield self.force_tip_expire()

        yield self.postpone_tip_expiration()

        yield cleaning_sched.CleaningSchedule().operation()

        yield self.test_postpone_survive_cleaning()

    @inlineCallbacks
    def test_itip_life_and_expire_with_files(self):
        # create tip but not rtips
        self.perform_submission_start()
        yield self.perform_submission_uploads()
        yield self.perform_submission_actions()

        self.assertTrue(os.listdir(GLSetting.submission_path) != [])

        yield self.check_tip_not_expired()
        yield self.force_tip_expire()

        yield cleaning_sched.CleaningSchedule().operation()

        self.assertTrue(os.listdir(GLSetting.submission_path) == [])
        self.assertTrue(os.listdir(GLSetting.tmp_upload_path) == [])

    @inlineCallbacks
    def test_rtip_life_and_expire_with_files(self):
        # create itip and rtips
        yield self.perform_full_submission_actions()

        self.assertTrue(os.listdir(GLSetting.submission_path) != [])

        yield self.check_tip_not_expired()
        yield self.force_tip_expire()

        yield cleaning_sched.CleaningSchedule().operation()

        self.assertTrue(os.listdir(GLSetting.submission_path) == [])
        self.assertTrue(os.listdir(GLSetting.tmp_upload_path) == [])
