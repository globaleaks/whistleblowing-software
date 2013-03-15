import re

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSetting
from globaleaks.tests import helpers

from globaleaks.rest import errors, requests
from globaleaks.rest.base import uuid_regexp
from globaleaks.handlers import tip, base, admin, submission, authentication
from globaleaks.jobs import delivery_sched
from globaleaks import models

class MockHandler(base.BaseHandler):

    def __init__(self):
        pass

class TTip(helpers.TestWithDB):

    # filled in setup
    context_desc = None
    receiver1_desc = receiver2_desc = None
    submission_desc = None

    # filled while the emulation tests
    receipt = None
    itip_id = wb_tip_id = rtip1_id = rtip2_id = None
    wb_data = receiver1_data = receiver2_data = None

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
        'wb_fields': {'headline': u'an headline', 'description': u'a dirty desky'},
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
    def setup_tip_environment(self):

        basehandler = MockHandler()

        basehandler.validate_jmessage(self.tipContext, requests.adminContextDesc)
        self.context_desc = yield admin.create_context(self.tipContext)

        self.tipReceiver1['contexts'] = self.tipReceiver2['contexts'] = [ self.context_desc['context_gus'] ]
        basehandler.validate_jmessage( self.tipReceiver1, requests.adminReceiverDesc )
        basehandler.validate_jmessage( self.tipReceiver2, requests.adminReceiverDesc )

        try:
            self.receiver1_desc = yield admin.create_receiver(self.tipReceiver1)
        except Exception, e:
            print e
            self.assertTrue(False)

        self.receiver2_desc = yield admin.create_receiver(self.tipReceiver2)

        self.assertEqual(self.receiver1_desc['contexts'], [ self.context_desc['context_gus']])
        self.assertEqual(self.receiver2_desc['contexts'], [ self.context_desc['context_gus']])

        self.tipSubmission['context_gus'] = self.context_desc['context_gus']
        basehandler.validate_jmessage( self.tipSubmission, requests.wbSubmissionDesc)

        self.submission_desc = yield submission.create_submission(self.tipSubmission, finalize=True)

        self.assertEqual(self.submission_desc['wb_fields'], self.tipSubmission['wb_fields'])
        self.assertEqual(self.submission_desc['mark'], models.InternalTip._marker[1])
        # Ok, now the submission has been finalized, the tests can start.

    @inlineCallbacks
    def get_wb_receipt_on_finalized(self):
        """
        emulate auth, get wb_tip.id, get the data like GET /tip/xxx
        """
        if not self.receipt:
            self.receipt = yield submission.create_whistleblower_tip(self.submission_desc)

        self.assertTrue(re.match(GLSetting.receipt_regexp, self.receipt) )

    @inlineCallbacks
    def wb_auth_with_receipt(self):

        if not self.wb_tip_id:
            self.get_wb_receipt_on_finalized()

            self.wb_tip_id = yield authentication.login_wb(self.receipt)
            # is the self.current_user['user_id']

        self.assertTrue(re.match(uuid_regexp, self.wb_tip_id))

    @inlineCallbacks
    def wb_auth_with_bad_receipt(self):

        fakereceipt = u"1234567890"
        try:
            yield authentication.login_wb(fakereceipt)
            self.assertTrue(False)
        except errors.InvalidAuthRequest:
            self.assertTrue(True)

    @inlineCallbacks
    def wb_retrive_tip_data(self):
        if not self.wb_tip_id:
            self.wb_auth_with_receipt()

        self.wb_data = yield tip.get_internaltip_wb(self.wb_tip_id)

        self.assertEqual(self.wb_data['fields'], self.submission_desc['wb_fields'])

    @inlineCallbacks
    def create_receivers_tip(self):

        receiver_tips = yield delivery_sched.tip_creation()

        self.rtip1_id = receiver_tips[0]
        self.rtip2_id = receiver_tips[1]

        self.assertEqual(len(receiver_tips), 2)
        self.assertTrue(re.match(uuid_regexp, receiver_tips[0]))
        self.assertTrue(re.match(uuid_regexp, receiver_tips[1]))

    @inlineCallbacks
    def access_receivers_tip(self):

        auth1 = yield authentication.login_receiver(self.receiver1_desc['username'], self.receiver1_desc['password'])
        self.assertEqual(auth1, self.receiver1_desc['receiver_gus'])

        auth2 = yield authentication.login_receiver(self.receiver2_desc['username'], self.receiver2_desc['password'])
        self.assertEqual(auth2, self.receiver2_desc['receiver_gus'])

        self.receiver1_data = yield tip.get_internaltip_receiver(auth1, self.rtip1_id)
        self.assertEqual(self.receiver1_data['fields'], self.submission_desc['wb_fields'])

        self.receiver2_data = yield tip.get_internaltip_receiver(auth2, self.rtip2_id)
        self.assertEqual(self.receiver2_data['fields'], self.submission_desc['wb_fields'])

    @inlineCallbacks
    def strong_receiver_auth(self):
        """
        Test that an authenticated Receiver1 can't access to the Tip generated for Rcvr2
        """

        # Instead of yield authentication.login_receiver(username/pasword), is used:
        auth_receiver_1 = self.receiver1_desc['receiver_gus']

        try:
            yield tip.get_internaltip_receiver(auth_receiver_1, self.rtip2_id)
            self.assertTrue(False)
        except errors.TipGusNotFound, e:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)

    @inlineCallbacks
    def increment_access_counter(self):
        """
        Receiver two access two time, and one access one time
        """
        counter = yield tip.increment_receiver_access_count(
                            self.receiver2_desc['receiver_gus'], self.rtip2_id)
        self.assertEqual(counter, 1)

        counter = yield tip.increment_receiver_access_count(
                            self.receiver2_desc['receiver_gus'], self.rtip2_id)
        self.assertEqual(counter, 2)

        counter = yield tip.increment_receiver_access_count(
                            self.receiver1_desc['receiver_gus'], self.rtip1_id)
        self.assertEqual(counter, 1)

    @inlineCallbacks
    def receiver1_express_positive_vote(self):
        vote_sum = yield tip.manage_pertinence(
            self.receiver1_desc['receiver_gus'], self.rtip1_id, True)
        self.assertEqual(vote_sum, 1)

    @inlineCallbacks
    def receiver2_express_negative_vote(self):
        vote_sum = yield tip.manage_pertinence(
            self.receiver2_desc['receiver_gus'], self.rtip2_id, False)
        self.assertEqual(vote_sum, 0)

    @inlineCallbacks
    def receiver2_fail_double_vote(self):
        try:
            yield tip.manage_pertinence(
                self.receiver2_desc['receiver_gus'], self.rtip2_id, False)
            self.assertTrue(False)
        except errors.TipPertinenceExpressed:
            self.assertTrue(True)

    @inlineCallbacks
    def receiver_2_get_banned_for_too_much_access(self):
        try:
            counter = yield tip.increment_receiver_access_count(
                self.receiver2_desc['receiver_gus'], self.rtip2_id)
            print counter
            self.assertTrue(False)
        except errors.AccessLimitExceeded:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e


    @inlineCallbacks
    def receiver1_RW_comments(self):
        self.commentCreation['content'] = unicode("Comment N1 by R1")
        yield tip.create_comment_receiver(
                                    self.receiver1_desc['receiver_gus'],
                                    self.rtip1_id,
                                    self.commentCreation)

        cl = yield tip.get_comment_list_receiver(
                                    self.receiver1_desc['receiver_gus'],
                                    self.rtip1_id)
        self.assertEqual(len(cl), 1)

        self.commentCreation['content'] = unicode("Comment N2 by R2")
        yield tip.create_comment_receiver(
                                    self.receiver2_desc['receiver_gus'],
                                    self.rtip2_id,
                                    self.commentCreation)

        cl = yield tip.get_comment_list_receiver(
                                    self.receiver2_desc['receiver_gus'],
                                    self.rtip2_id)
        self.assertEqual(len(cl), 2)


    @inlineCallbacks
    def wb_RW_comments(self):
        self.commentCreation['content'] = unicode("I'm a WB comment")
        yield tip.create_comment_wb(self.wb_tip_id, self.commentCreation)

        cl = yield tip.get_comment_list_wb(self.wb_tip_id)
        self.assertEqual(len(cl), 3)

    @inlineCallbacks
    def receiver2_fail_in_delete_internal_tip(self):
        try:
            yield tip.delete_internal_tip(self.receiver2_desc['receiver_gus'],
                                    self.rtip2_id)
            self.assertTrue(False)
        except errors.ForbiddenOperation:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e

    @inlineCallbacks
    def receiver2_personal_delete(self):
        yield tip.delete_receiver_tip(self.receiver2_desc['receiver_gus'], self.rtip2_id)


    @inlineCallbacks
    def receiver1_see_system_comments(self):
        cl = yield tip.get_comment_list_receiver(self.receiver1_desc['receiver_gus'],
                                        self.rtip1_id)

        self.assertEqual(len(cl), 4)
        self.assertEqual(cl[0]['source'], models.Comment._types[0]) # Receiver (Rcvr1)
        self.assertEqual(cl[1]['source'], models.Comment._types[0]) # Receiver (Rcvr2)
        self.assertEqual(cl[2]['source'], models.Comment._types[1]) # Wb
        self.assertEqual(cl[3]['source'], models.Comment._types[2]) # System


    @inlineCallbacks
    def receiver1_total_delete_tip(self):

        yield tip.delete_internal_tip(self.receiver1_desc['receiver_gus'],
            self.rtip1_id)

        try:
            # just one operation that fail if iTip is invalid
            yield tip.get_internaltip_receiver(
                        self.receiver1_desc['receiver_gus'], self.rtip1_id)
            self.assertTrue(False)
        except errors.TipGusNotFound:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e

    @inlineCallbacks
    def test_full_receiver_wb_workflow(self):
        yield self.setup_tip_environment()
        yield self.get_wb_receipt_on_finalized()
        yield self.wb_auth_with_receipt()
        yield self.wb_auth_with_bad_receipt()
        yield self.wb_retrive_tip_data()
        yield self.create_receivers_tip()
        yield self.access_receivers_tip()
        yield self.strong_receiver_auth()
        yield self.increment_access_counter()
        yield self.receiver1_express_positive_vote()
        yield self.receiver2_express_negative_vote()
        yield self.receiver2_fail_double_vote()
        yield self.receiver_2_get_banned_for_too_much_access()
        yield self.receiver1_RW_comments()
        yield self.wb_RW_comments()
        yield self.receiver2_fail_in_delete_internal_tip()
        yield self.receiver2_personal_delete()
        yield self.receiver1_see_system_comments()
        yield self.receiver1_total_delete_tip()
