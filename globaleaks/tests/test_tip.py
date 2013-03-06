import re

from storm.twisted.testing import FakeThreadPool
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

from globaleaks.rest import errors, requests
from globaleaks.rest.base import uuid_regexp
from globaleaks.handlers import tip, base, admin, submission, authentication
from globaleaks.jobs import delivery_sched
from globaleaks import models, db
from globaleaks.settings import GLSetting, transact

_TEST_DB = 'tiponlytest.db'
transact.tp = FakeThreadPool()
GLSetting.scheduler_threadpool = FakeThreadPool()
GLSetting.db_file = 'sqlite:///' + _TEST_DB
GLSetting.store = 'test_store'
GLSetting.notification_plugins = []

class MockHandler(base.BaseHandler):

    def __init__(self):
        pass

class TTip(unittest.TestCase):

    # filled in setup
    context_desc = None
    receiver1_desc = receiver2_desc = None
    submission_desc = None

    # filled while the emulation tests
    receipt = None
    itip_id = wb_tip_id = rtip1_id = rtip2_id = None
    wb_data = receiver1_data = receiver2_data = None

    @inlineCallbacks
    def initalize_db(self):
        try:
            yield db.createTables(create_node=True)
        except Exception, e:
            print "Fatal: unable to createTables [%s]" % str(e)
            raise e


    # These dummy variables follow
    # indeed in a different style
    # are used in the tip hollow
    # and is not a pattern defile

    tipContext = {
        'name': u'CtxName', 'description': u'dummy context with default fields',
        'escalation_threshold': u'1', 'tip_max_access': u'2',
        'tip_timetolive': 1, 'file_max_download': 2, 'selectable_receiver': False,
        'receivers': [], 'fields': []
    }

    tipReceiver1 = {
        'notification_fields': {'mail_address': u'first@winstonsmith.org' },
        'name': u'first', 'description': u"I'm tha 1st",
        'receiver_level': u'1', 'can_delete_submission': True,
        'password': u'x'
    }

    tipReceiver2 = {
        'notification_fields': {'mail_address': u'second@winstonsmith.org' },
        'name': u'second', 'description': u"I'm tha 2nd",
        'receiver_level': u'1', 'can_delete_submission': False,
        'password': u'x'
    }

    tipSubmission = {
        'wb_fields': {'headline': u'an headline', 'Sun': u'a Sun'},
        'context_gus': '', 'receivers': [], 'files': [], 'finalize': True
    }

    tipOptions = {
        'total_delete': False,
        'is_pertinent': False,
    }

    commentCreation = {
        'content': '',
    }


class TestTipInstance(TTip):
    _handler = tip.TipInstance

    # Test model is a prerequisite for create e valid environment where Tip lives

    # The test environment has one context (escalation 1, tip TTL 2, max file download 1)
    #                          two receiver ("first" level 1, "second" level 2)
    # Test context would just contain two receiver, one level 1 and the other level 2

    # They are defined in TTip. This unitTest DO NOT TEST HANDLERS but transaction functions

    @inlineCallbacks
    def test_1_setup_tip_environment(self):

        self.initalize_db()
        basehandler = MockHandler()

        basehandler.validate_jmessage( TTip.tipContext, requests.adminContextDesc)
        TTip.context_desc = yield admin.create_context(TTip.tipContext)

        TTip.tipReceiver1['contexts'] = TTip.tipReceiver2['contexts'] = [ TTip.context_desc['context_gus'] ]
        basehandler.validate_jmessage( TTip.tipReceiver1, requests.adminReceiverDesc )
        basehandler.validate_jmessage( TTip.tipReceiver2, requests.adminReceiverDesc )
        TTip.receiver1_desc = yield admin.create_receiver(TTip.tipReceiver1)
        TTip.receiver2_desc = yield admin.create_receiver(TTip.tipReceiver2)

        self.assertEqual(TTip.receiver1_desc['contexts'], [ TTip.context_desc['context_gus']])
        self.assertEqual(TTip.receiver2_desc['contexts'], [ TTip.context_desc['context_gus']])

        TTip.tipSubmission['context_gus'] = TTip.context_desc['context_gus']
        basehandler.validate_jmessage( TTip.tipSubmission, requests.wbSubmissionDesc)
        TTip.submission_desc = yield submission.create_submission(TTip.tipSubmission, finalize=True)

        self.assertEqual(TTip.submission_desc['wb_fields'], TTip.tipSubmission['wb_fields'])
        self.assertEqual(TTip.submission_desc['mark'], models.InternalTip._marker[1])
        # Ok, now the submission has been finalized, the tests can start.

    @inlineCallbacks
    def test_2_get_wb_receipt_on_finalized(self):
        """
        emulate auth, get wb_tip.id, get the data like GET /tip/xxx
        """
        if not TTip.receipt:
            TTip.receipt = yield submission.create_whistleblower_tip(TTip.submission_desc)

        self.assertTrue(re.match('(\w+){10}', TTip.receipt) )

    @inlineCallbacks
    def test_3_wb_auth_with_receipt(self):

        if not TTip.wb_tip_id:
            self.test_2_get_wb_receipt_on_finalized()

            TTip.wb_tip_id = yield authentication.login_wb(TTip.receipt)
            # is the self.current_user['user_id']

        self.assertTrue(re.match(uuid_regexp, TTip.wb_tip_id))

    @inlineCallbacks
    def test_4_wb_auth_with_bad_receipt(self):

        fakereceipt = u"1234567890"
        try:
            yield authentication.login_wb(fakereceipt)
            self.assertTrue(False)
        except errors.InvalidAuthRequest:
            self.assertTrue(True)

    @inlineCallbacks
    def test_5_wb_retrive_tip_data(self):
        if not TTip.wb_tip_id:
            self.test_3_wb_auth_with_receipt()

        TTip.wb_data = yield tip.get_internaltip_wb(TTip.wb_tip_id)

        self.assertEqual(self.wb_data['fields'], TTip.submission_desc['wb_fields'])

    @inlineCallbacks
    def test_6_create_receivers_tip(self):

        receiver_tips = yield delivery_sched.tip_creation()

        TTip.rtip1_id = receiver_tips[0]
        TTip.rtip2_id = receiver_tips[1]

        self.assertEqual(len(receiver_tips), 2)
        self.assertTrue(re.match(uuid_regexp, receiver_tips[0]))
        self.assertTrue(re.match(uuid_regexp, receiver_tips[1]))

    @inlineCallbacks
    def test_7_access_receivers_tip(self):

        auth1 = yield authentication.login_receiver(TTip.receiver1_desc['username'], TTip.receiver1_desc['password'])
        self.assertEqual(auth1, TTip.receiver1_desc['receiver_gus'])

        auth2 = yield authentication.login_receiver(TTip.receiver2_desc['username'], TTip.receiver2_desc['password'])
        self.assertEqual(auth2, TTip.receiver2_desc['receiver_gus'])

        TTip.receiver1_data = yield tip.get_internaltip_receiver(auth1, TTip.rtip1_id)
        self.assertEqual(TTip.receiver1_data['fields'], TTip.submission_desc['wb_fields'])

        TTip.receiver2_data = yield tip.get_internaltip_receiver(auth2, TTip.rtip2_id)
        self.assertEqual(TTip.receiver2_data['fields'], TTip.submission_desc['wb_fields'])

    @inlineCallbacks
    def test_8_strong_receiver_auth(self):
        """
        Test that an authenticated Receiver1 can't access to the Tip generated for Rcvr2
        """

        # Instead of yield authentication.login_receiver(username/pasword), is used:
        auth_receiver_1 = TTip.receiver1_desc['receiver_gus']

        try:
            yield tip.get_internaltip_receiver(auth_receiver_1, TTip.rtip2_id)
            self.assertTrue(False)
        except errors.TipGusNotFound, e:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)

    @inlineCallbacks
    def test_8_increment_access_counter(self):
        """
        Receiver two access two time, and one access one time
        """
        counter = yield tip.increment_receiver_access_count(
                            TTip.receiver2_desc['receiver_gus'], TTip.rtip2_id)
        self.assertEqual(counter, 1)

        counter = yield tip.increment_receiver_access_count(
                            TTip.receiver2_desc['receiver_gus'], TTip.rtip2_id)
        self.assertEqual(counter, 2)

        counter = yield tip.increment_receiver_access_count(
                            TTip.receiver1_desc['receiver_gus'], TTip.rtip1_id)
        self.assertEqual(counter, 1)

    @inlineCallbacks
    def test_9_receiver1_express_positive_vote(self):
        vote_sum = yield tip.manage_pertinence(
            TTip.receiver1_desc['receiver_gus'], TTip.rtip1_id, True)
        self.assertEqual(vote_sum, 1)

    @inlineCallbacks
    def test_9_receiver2_express_negative_vote(self):
        vote_sum = yield tip.manage_pertinence(
            TTip.receiver2_desc['receiver_gus'], TTip.rtip2_id, False)
        self.assertEqual(vote_sum, 0)

    @inlineCallbacks
    def test_A_receiver2_fail_double_vote(self):
        try:
            yield tip.manage_pertinence(
                TTip.receiver2_desc['receiver_gus'], TTip.rtip2_id, False)
            self.assertTrue(False)
        except errors.TipPertinenceExpressed:
            self.assertTrue(True)

    @inlineCallbacks
    def test_B_receiver_2_get_banned_for_too_much_access(self):
        try:
            counter = yield tip.increment_receiver_access_count(
                TTip.receiver2_desc['receiver_gus'], TTip.rtip2_id)
            print counter
            self.assertTrue(False)
        except errors.AccessLimitExceeded:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e


    @inlineCallbacks
    def test_C_receiver1_RW_comments(self):
        TTip.commentCreation['content'] = unicode("Comment N1 by R1")
        yield tip.create_comment_receiver(
                                    TTip.receiver1_desc['receiver_gus'],
                                    TTip.rtip1_id,
                                    TTip.commentCreation)

        cl = yield tip.get_comment_list_receiver(
                                    TTip.receiver1_desc['receiver_gus'],
                                    TTip.rtip1_id)
        self.assertEqual(len(cl), 1)

        TTip.commentCreation['content'] = unicode("Comment N2 by R2")
        yield tip.create_comment_receiver(
                                    TTip.receiver2_desc['receiver_gus'],
                                    TTip.rtip2_id,
                                    TTip.commentCreation)

        cl = yield tip.get_comment_list_receiver(
                                    TTip.receiver2_desc['receiver_gus'],
                                    TTip.rtip2_id)
        self.assertEqual(len(cl), 2)


    @inlineCallbacks
    def test_C_wb_RW_comments(self):
        TTip.commentCreation['content'] = unicode("I'm a WB comment")
        yield tip.create_comment_wb(TTip.wb_tip_id, TTip.commentCreation)

        cl = yield tip.get_comment_list_wb(TTip.wb_tip_id)
        self.assertEqual(len(cl), 3)

    @inlineCallbacks
    def test_D_receiver2_fail_in_delete_internal_tip(self):
        try:
            yield tip.delete_internal_tip(TTip.receiver2_desc['receiver_gus'],
                                    TTip.rtip2_id)
            self.assertTrue(False)
        except errors.ForbiddenOperation:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e

    @inlineCallbacks
    def test_E_receiver2_personal_delete(self):
        yield tip.delete_receiver_tip(TTip.receiver2_desc['receiver_gus'], TTip.rtip2_id)


    @inlineCallbacks
    def test_F_receiver1_see_system_comments(self):
        cl = yield tip.get_comment_list_receiver(TTip.receiver1_desc['receiver_gus'],
                                        TTip.rtip1_id)

        self.assertEqual(len(cl), 4)
        self.assertEqual(cl[0]['source'], models.Comment._types[0]) # Receiver (Rcvr1)
        self.assertEqual(cl[1]['source'], models.Comment._types[0]) # Receiver (Rcvr2)
        self.assertEqual(cl[2]['source'], models.Comment._types[1]) # Wb
        self.assertEqual(cl[3]['source'], models.Comment._types[2]) # System


    @inlineCallbacks
    def test_G_receiver1_total_delete_tip(self):

        yield tip.delete_internal_tip(TTip.receiver1_desc['receiver_gus'],
            TTip.rtip1_id)

        try:
            # just one operation that fail if iTip is invalid
            yield tip.get_internaltip_receiver(
                        TTip.receiver1_desc['receiver_gus'], TTip.rtip1_id)
            self.assertTrue(False)
        except errors.TipGusNotFound:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e
