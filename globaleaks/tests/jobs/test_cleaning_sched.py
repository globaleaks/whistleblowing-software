# -*- encoding: utf-8 -*-
import os

import copy

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers

from globaleaks import models
from globaleaks.rest import requests
from globaleaks.handlers import base, admin, submission, files, rtip, receiver
from globaleaks.jobs import delivery_sched, cleaning_sched
from globaleaks.utils.utility import is_expired, datetime_null
from globaleaks.settings import transact, GLSetting
from globaleaks.tests.test_tip import TTip

from globaleaks.security import GLSecureTemporaryFile

STATIC_PASSWORD = u'bungabunga ;('
dummy_sum = u'a1c2257ef58acffec9b0e2d165dc6be67c8d05f224116714e18bec972aea34c3'

class MockHandler(base.BaseHandler):

    def __init__(self):
        pass

class TTip(helpers.TestGL):

    # filled in setup
    context_desc = None
    receiver1_desc = receiver2_desc = None
    submission_desc = None

    # filled while the emulation tests
    receipt = None
    itip_id = wb_tip_id = rtip1_id = rtip2_id = None
    wb_data = receiver1_data = receiver2_data = None

    # https://www.youtube.com/watch?v=ja46oa2ZML8 couple of cups, and tests!:

    tipContext = TTip.tipContext
    tipReceiver1 = copy.deepcopy(TTip.tipReceiver1)
    tipReceiver1['postpone_superpower'] = True
    tipReceiver2 = copy.deepcopy(TTip.tipReceiver2)
    tipReceiver2['postpone_superpower'] = True
    tipOptions = TTip.tipOptions
    commentCreation = TTip.commentCreation

class TestCleaning(TTip):

    # Test model is a prerequisite for create e valid environment where Tip lives

    # The test environment has one context (escalation 1, tip TTL 2, max file download 1)
    #                          two receiver ("first" level 1, "second" level 2)
    # Test context would just contain two receiver, one level 1 and the other level 2

    # They are defined in TTip. This unitTest DO NOT TEST HANDLERS but transaction functions

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
    def force_submission_expire(self, store):
        tips = store.find(models.InternalTip)
        for tip in tips:
            tip.creation_date = datetime_null()
            self.assertTrue(is_expired(tip.creation_date))

    @transact
    def force_tip_expire(self, store):
        tips = store.find(models.InternalTip)
        for tip in tips:
            tip.expiration_date = datetime_null()
            self.assertTrue(is_expired(tip.expiration_date))

    @inlineCallbacks
    def do_setup_tip_environment(self):

        basehandler = MockHandler()

        for attrname in models.Context.localized_strings:
            self.tipContext[attrname] = u'⅛¡⅜⅛’ŊÑŦŊŊ’‘ª‘ª’‘ÐŊ'

        basehandler.validate_jmessage(self.tipContext, requests.adminContextDesc)
        self.context_desc = yield admin.create_context(self.tipContext)

        self.tipReceiver1['contexts'] = self.tipReceiver2['contexts'] = [ self.context_desc['id'] ]

        for attrname in models.Receiver.localized_strings:
            self.tipReceiver2[attrname] = u'222222’‘ª‘ª’‘ÐŊ'
            self.tipReceiver1[attrname] = u'⅛¡⅜⅛’ŊÑŦŊ1111111’‘ª‘ª’‘ÐŊ'

        basehandler.validate_jmessage( self.tipReceiver1, requests.adminReceiverDesc )
        basehandler.validate_jmessage( self.tipReceiver2, requests.adminReceiverDesc )

        try:
            self.receiver1_desc = yield admin.create_receiver(self.tipReceiver1)
            self.receiver2_desc = yield admin.create_receiver(self.tipReceiver2)
        except Exception as exxxx:
            self.assertTrue(False)

        self.assertEqual(self.receiver1_desc['contexts'], [ self.context_desc['id']])
        self.assertEqual(self.receiver2_desc['contexts'], [ self.context_desc['id']])

        dummySubmission = helpers.get_dummy_submission(self.context_desc['id'], self.context_desc['fields'])
        basehandler.validate_jmessage( dummySubmission, requests.wbSubmissionDesc)

        self.submission_desc = yield submission.create_submission(dummySubmission, finalize=False)

        self.assertEqual(self.submission_desc['wb_fields'], dummySubmission['wb_fields'])
        self.assertEqual(self.submission_desc['mark'], models.InternalTip._marker[0])

    @inlineCallbacks
    def do_finalize_submission(self):
        self.submission_desc['finalize'] = True
        self.submission_desc['wb_fields'] = helpers.fill_random_fields(self.context_desc)
        self.submission_desc = yield submission.update_submission(
            self.submission_desc['id'],
            self.submission_desc,
            finalize=True)

        self.assertEqual(self.submission_desc['mark'], models.InternalTip._marker[1])
        
        submission.create_whistleblower_tip(self.submission_desc)

    # -------------------------------------------
    # Those the two class implements the sequence
    # -------------------------------------------

class TipCleaning(TestCleaning):

    @inlineCallbacks
    def postpone_tip_expiration(self):
        recv_desc = yield admin.get_receiver_list()
        self.assertEqual(len(recv_desc), 2)
        rtip_desc = yield receiver.get_receiver_tip_list(recv_desc[0]['id'])
        self.assertEqual(len(rtip_desc), 1)
        tip_list = yield cleaning_sched.get_tiptime_by_marker(models.InternalTip._marker[2])
        self.assertEqual(len(tip_list), 1)
        rtip.postpone_expiration_date(recv_desc[0]['id'], rtip_desc[0]['id'])

        yield cleaning_sched.CleaningSchedule().operation()

    @inlineCallbacks
    def test_001_unfinished_submission_life_and_expire(self):
        yield self.do_setup_tip_environment()
        yield self.check_tip_not_expired()
        yield self.force_submission_expire()
        yield cleaning_sched.CleaningSchedule().operation()
        yield self.test_cleaning()

    @inlineCallbacks
    def test_002_tip_life_and_expire(self):
        yield self.do_setup_tip_environment()       
        yield self.do_finalize_submission()

        yield delivery_sched.DeliverySchedule().operation()

        yield self.check_tip_not_expired()
        yield self.force_tip_expire()

        yield cleaning_sched.CleaningSchedule().operation()

        yield self.test_cleaning()

    @inlineCallbacks
    def test_003_tip_life_postpone(self):
        yield self.do_setup_tip_environment()
        yield self.do_finalize_submission()

        yield delivery_sched.DeliverySchedule().operation()

        yield self.check_tip_not_expired()
        yield self.force_tip_expire()
        yield self.postpone_tip_expiration()

        yield cleaning_sched.CleaningSchedule().operation()

        yield self.test_postpone_survive_cleaning()

    @inlineCallbacks
    def test_004_tip_life_and_expire_with_files(self):
        yield self.do_setup_tip_environment()

        yield self.emulate_file_upload(self.submission_desc['id'])

        yield self.do_finalize_submission()

        yield delivery_sched.DeliverySchedule().operation()

        self.assertTrue(os.listdir(GLSetting.submission_path) != [])

        yield self.check_tip_not_expired()

        yield self.force_tip_expire()

        yield cleaning_sched.CleaningSchedule().operation()

        self.assertTrue(os.listdir(GLSetting.submission_path) == [])
        self.assertTrue(os.listdir(GLSetting.tmp_upload_path) == [])
