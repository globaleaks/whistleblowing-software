# -*- encoding: utf-8 -*-
import re
from datetime import datetime

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSetting
from globaleaks.tests import helpers
from globaleaks.rest import errors, requests
from globaleaks.handlers import base, admin, submission, authentication, receiver, rtip, wbtip
from globaleaks.jobs import delivery_sched
from globaleaks import models
STATIC_PASSWORD = u'bungabunga ;( 12345'

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

    # These dummy variables follow
    # indeed in a different style
    # are used in the tip hollow
    # and is not a pattern defile

    dummySteps = [{
        'label': u'Presegnalazione',
        'description': u'',
        'hint': u'',
        'children': [u'd4f06ad1-eb7a-4b0d-984f-09373520cce7',
                     u'c4572574-6e6b-4d86-9a2a-ba2e9221467d',
                     u'6a6e9282-15e8-47cd-9cc6-35fd40a4a58f']
        },
        {
          'label': u'Segnalazione',
          'description': u'',
          'hint': u'',
          'children': []
        }
    ]

    tipContext = {
        'name': u'CtxName', 'description': u'dummy context with default fields',
        'escalation_threshold': 1,
        'tip_max_access': 2, 
        'tip_timetolive': 200, 'file_max_download': 2, 'selectable_receiver': False,
        'receivers': [], 'submission_timetolive': 100,
        'file_required': False, 'tags' : [ u'one', u'two', u'y' ],
        'select_all_receivers': True,
        'receiver_introduction': u"¡⅜⅛⅝⅞⅝⅛⅛¡⅛⅛⅛",
        'postpone_superpower': False,
        'can_delete_submission': False,
        'maximum_selectable_receivers': 0,
        'require_file_description': False,
        'delete_consensus_percentage': 0,
        'require_pgp': False,
        'show_small_cards': False,
        'show_receivers': True,
        'enable_private_messages': True,
        'presentation_order': 0,
        'steps': dummySteps
    }

    tipReceiver1 = {
        'mail_address': u'first@winstonsmith.org',
        'name': u'first', 'description': u"I'm tha 1st",
        'receiver_level': u'1', 'can_delete_submission': True,
        'password': STATIC_PASSWORD, 'tags': [], 'file_notification': False,
        'comment_notification': True, 'tip_notification': False, 'gpg_key_status': u'Disabled',
        'message_notification': True,
        'postpone_superpower': False,
        'gpg_key_info': None, 'gpg_key_fingerprint': None,
        'gpg_key_remove': False, 'gpg_key_armor': None, 'gpg_enable_notification': False,
        'presentation_order': 0,
        'timezone': 0,
        'language': u'en'
    }

    tipReceiver2 = {
        'mail_address': u'second@winstonsmith.org',
        'name': u'second', 'description': u"I'm tha 2nd",
        'receiver_level': u'1', 'can_delete_submission': False,
        'password': STATIC_PASSWORD, 'tags': [], 'file_notification': False,
        'message_notification': True,
        'postpone_superpower': True,
        'comment_notification': True, 'tip_notification': False, 'gpg_key_status': u'Disabled',
        'gpg_key_info': None, 'gpg_key_fingerprint': None,
        'gpg_key_remove': False, 'gpg_key_armor': None, 'gpg_enable_notification': False,
        'presentation_order': 0,
        'timezone': 0,
        'language': u'en'
    }

    tipOptions = {
        'global_delete': False,
        'is_pertinent': False,
    }

    commentCreation = {
        'content': '',
    }

class TestTipInstance(TTip):

    # Test model is a prerequisite for create e valid environment where Tip lives

    # The test environment has one context (escalation 1, tip TTL 2, max file download 1)
    #                          two receiver ("first" level 1, "second" level 2)
    # Test context would just contain two receiver, one level 1 and the other level 2

    # They are defined in TTip. This unitTest DO NOT TEST HANDLERS but transaction functions

    @inlineCallbacks
    def setup_tip_environment(self):

        basehandler = MockHandler()

        stuff = u'⅛⅛⅛£"$"$¼³²¼²³¼²³“““““ð'
        for attrname in models.Context.localized_strings:
            self.tipContext[attrname] = stuff

        basehandler.validate_jmessage(self.tipContext, requests.adminContextDesc)

        # the test context need fields to be present
        from globaleaks.handlers.admin.field import create_field
        for idx, field in enumerate(self.dummyFields):
            f = yield create_field(field, 'en')
            self.dummyFields[idx]['id'] = f['id']

        self.tipContext['steps'][0]['children'] = [
            self.dummyFields[0]['id'], # Field 1
            self.dummyFields[1]['id'], # Field 2
            self.dummyFields[4]['id']  # Generalities
        ]

        self.context_desc = yield admin.create_context(self.tipContext)

        self.tipReceiver1['contexts'] = self.tipReceiver2['contexts'] = [ self.context_desc['id'] ]

        for attrname in models.Receiver.localized_strings:
            self.tipReceiver1[attrname] = stuff
            self.tipReceiver2[attrname] = stuff

        basehandler.validate_jmessage( self.tipReceiver1, requests.adminReceiverDesc )
        basehandler.validate_jmessage( self.tipReceiver2, requests.adminReceiverDesc )

        self.receiver1_desc = yield admin.create_receiver(self.tipReceiver1)
        self.receiver2_desc = yield admin.create_receiver(self.tipReceiver2)

        self.assertEqual(self.receiver1_desc['contexts'], [ self.context_desc['id']])

        dummySubmissionDict = yield self.get_dummy_submission(self.context_desc['id'])
        basehandler.validate_jmessage(dummySubmissionDict, requests.wbSubmissionDesc)

        self.submission_desc = yield submission.create_submission(dummySubmissionDict, finalize=True)

        self.assertEqual(self.submission_desc['wb_steps'], dummySubmissionDict['wb_steps'])
        self.assertEqual(self.submission_desc['mark'], models.InternalTip._marker[1])
        # Ok, now the submission has been finalized, the tests can start.

    @inlineCallbacks
    def get_wb_receipt_on_finalized(self):
        """
        emulate auth, get wb_tip.id, get the data like GET /tip/xxx
        """
        if not self.receipt:
            self.receipt = yield submission.create_whistleblower_tip(self.submission_desc)

        self.assertGreater(len(self.receipt), 5)
        self.assertTrue(re.match(self.dummyNode['receipt_regexp'], self.receipt) )

    @inlineCallbacks
    def wb_auth_with_receipt(self):

        if not self.wb_tip_id:
            self.get_wb_receipt_on_finalized()

            self.wb_tip_id = yield authentication.login_wb(self.receipt)
            # is the self.current_user.user_id

        self.assertTrue(re.match(requests.uuid_regexp, self.wb_tip_id))

    @inlineCallbacks
    def wb_auth_with_bad_receipt(self):

        fakereceipt = u"1234567890AA"

        retval = yield authentication.login_wb(fakereceipt)
        self.assertFalse(retval)

    @inlineCallbacks
    def wb_retrive_tip_data(self):
        if not self.wb_tip_id:
            self.wb_auth_with_receipt()

        self.wb_data = yield wbtip.get_internaltip_wb(self.wb_tip_id)

        self.assertEqual(self.wb_data['wb_steps'], self.submission_desc['wb_steps'])

    @inlineCallbacks
    def create_receivers_tip(self):

        receiver_tips = yield delivery_sched.tip_creation()

        self.rtip1_id = receiver_tips[0]
        self.rtip2_id = receiver_tips[1]

        self.assertEqual(len(receiver_tips), 2)
        self.assertTrue(re.match(requests.uuid_regexp, receiver_tips[0]))
        self.assertTrue(re.match(requests.uuid_regexp, receiver_tips[1]))

    @inlineCallbacks
    def access_receivers_tip(self):

        auth1, _ = yield authentication.login_receiver(self.receiver1_desc['username'], STATIC_PASSWORD)
        self.assertEqual(auth1, self.receiver1_desc['id'])

        auth2, _ = yield authentication.login_receiver(self.receiver2_desc['username'], STATIC_PASSWORD)
        self.assertEqual(auth2, self.receiver2_desc['id'])

        # we does not know the association auth# sefl.rtip#_id
        # so we need a double try catch for each check and we need to store the proper association
        tmp1 = self.rtip1_id
        tmp2 = self.rtip2_id
        try:
            self.receiver1_data = yield rtip.get_internaltip_receiver(auth1, tmp1)
        except:
            self.rtip1_id = tmp2
            self.rtip2_id = tmp1

            self.receiver1_data = yield rtip.get_internaltip_receiver(auth1, tmp2)

            self.assertEqual(self.receiver1_data['wb_steps'], self.submission_desc['wb_steps'])
            self.assertEqual(self.receiver1_data['access_counter'], 0)

        self.receiver2_data = yield rtip.get_internaltip_receiver(auth2, self.rtip2_id)
        self.assertEqual(self.receiver2_data['wb_steps'], self.submission_desc['wb_steps'])
        self.assertEqual(self.receiver2_data['access_counter'], 0)

    @inlineCallbacks
    def strong_receiver_auth(self):
        """
        Test that an authenticated Receiver1 can't access to the Tip generated for Rcvr2
        """

        # Instead of yield authentication.login_receiver(username/pasword), is used:
        auth_receiver_1 = self.receiver1_desc['id']

        yield self.assertFailure(rtip.get_internaltip_receiver(auth_receiver_1, self.rtip2_id),
                                 errors.TipIdNotFound)

    @inlineCallbacks
    def increment_access_counter(self):
        """
        Receiver two access two time, and one access one time
        """
        counter = yield rtip.increment_receiver_access_count(
                            self.receiver2_desc['id'], self.rtip2_id)
        self.assertEqual(counter, 1)

        counter = yield rtip.increment_receiver_access_count(
                            self.receiver2_desc['id'], self.rtip2_id)
        self.assertEqual(counter, 2)

        counter = yield rtip.increment_receiver_access_count(
                            self.receiver1_desc['id'], self.rtip1_id)
        self.assertEqual(counter, 1)

    @inlineCallbacks
    def receiver1_express_positive_vote(self):
        vote_sum = yield rtip.manage_pertinence(
            self.receiver1_desc['id'], self.rtip1_id, True)
        self.assertEqual(vote_sum, 1)

    @inlineCallbacks
    def receiver1_get_tip_list(self):
        tiplist = yield receiver.get_receiver_tip_list(self.receiver1_desc['id'])

        # this test has been added to test issue/515
        self.assertTrue(isinstance(tiplist, list))
        self.assertTrue(isinstance(tiplist[0], dict))
        self.assertTrue(isinstance(tiplist[0]['preview'], list))
        # then the content here depends on the fields

    @inlineCallbacks
    def receiver2_express_negative_vote(self):
        vote_sum = yield rtip.manage_pertinence(
            self.receiver2_desc['id'], self.rtip2_id, False)
        self.assertEqual(vote_sum, 0)

    @inlineCallbacks
    def receiver2_fail_double_vote(self):
        try:
            yield rtip.manage_pertinence(
                self.receiver2_desc['id'], self.rtip2_id, False)
            self.assertTrue(False)
        except errors.TipPertinenceExpressed:
            self.assertTrue(True)

    @inlineCallbacks
    def receiver_2_get_banned_for_too_much_access(self):
        try:
            counter = yield rtip.increment_receiver_access_count(
                self.receiver2_desc['id'], self.rtip2_id)
            self.assertTrue(False)
        except errors.AccessLimitExceeded:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e


    @inlineCallbacks
    def receiver_RW_comments(self):
        self.commentCreation['content'] = unicode("Comment N1 by R1")
        yield rtip.create_comment_receiver(
                                    self.receiver1_desc['id'],
                                    self.rtip1_id,
                                    self.commentCreation)

        cl = yield rtip.get_comment_list_receiver(
                                    self.receiver1_desc['id'],
                                    self.rtip1_id)
        self.assertEqual(len(cl), 1)

        self.commentCreation['content'] = unicode("Comment N2 by R2")
        yield rtip.create_comment_receiver(
                                    self.receiver2_desc['id'],
                                    self.rtip2_id,
                                    self.commentCreation)

        cl = yield rtip.get_comment_list_receiver(
                                    self.receiver2_desc['id'],
                                    self.rtip2_id)
        self.assertEqual(len(cl), 2)

    @inlineCallbacks
    def wb_RW_comments(self):
        self.commentCreation['content'] = unicode("I'm a WB comment")
        yield wbtip.create_comment_wb(self.wb_tip_id, self.commentCreation)

        cl = yield wbtip.get_comment_list_wb(self.wb_tip_id)
        self.assertEqual(len(cl), 3)

    @inlineCallbacks
    def wb_get_receiver_list(self, default_lang):
        receiver_list = yield wbtip.get_receiver_list_wb(self.wb_tip_id, default_lang)
        self.assertEqual(len(receiver_list), 2)
        self.assertEqual(receiver_list[0]['access_counter'] + receiver_list[1]['access_counter'], 3)

    @inlineCallbacks
    def receiver_get_receiver_list(self, default_lang):
        receiver_list = yield rtip.get_receiver_list_receiver(self.receiver1_desc['id'], self.rtip1_id, default_lang)
        self.assertEqual(len(receiver_list), 2)
        self.assertEqual(receiver_list[0]['access_counter'] + receiver_list[1]['access_counter'], 3)

        receiver_list = yield rtip.get_receiver_list_receiver(self.receiver2_desc['id'], self.rtip2_id, default_lang)
        self.assertEqual(len(receiver_list), 2)
        self.assertEqual(receiver_list[0]['access_counter'] + receiver_list[1]['access_counter'], 3)

    @inlineCallbacks
    def fail_postpone_expiration_date(self):
        tip_expiring = yield rtip.get_internaltip_receiver(
            self.receiver1_desc['id'], self.rtip1_id)

        yield self.assertFailure(rtip.postpone_expiration_date(
                                     self.receiver1_desc['id'],
                                     self.rtip1_id),
                                 errors.ExtendTipLifeNotEnabled)

        tip_not_extended = yield rtip.get_internaltip_receiver(
            self.receiver1_desc['id'], self.rtip1_id)

        self.assertEqual(tip_expiring['expiration_date'], tip_not_extended['expiration_date'])

    @inlineCallbacks
    def verify_default_expiration_date(self):
        """
        that's the date status in this test (tip ttl 200 days)

        creation_date : 2013-10-31T21:22:14.481809
        potential_expiration_date : 2014-05-19 21:22:16.677997
        expiration_date : 2014-05-19T21:22:14.481711
        """
        context_list = yield admin.get_context_list()
        self.assertTrue(isinstance(context_list, list))
        self.assertEqual(len(context_list), 1)
        tip_ttl = context_list[0]['tip_timetolive']

        tip_expiring = yield rtip.get_internaltip_receiver(
            self.receiver1_desc['id'], self.rtip1_id)

        # TODO implement a more complete test

    @inlineCallbacks
    def update_node_properties(self):
        node_desc = yield admin.admin_serialize_node()
        self.assertEqual(node_desc['postpone_superpower'], False)
        node_desc['postpone_superpower'] = True

        stuff = u"³²¼½¬¼³²"
        for attrname in models.Node.localized_strings:
            node_desc[attrname] = stuff

        node_desc = yield admin.update_node(node_desc)
        self.assertEqual(node_desc['postpone_superpower'], True)

    @inlineCallbacks
    def success_postpone_expiration_date(self):
        """
        Tests with receiver1 and update with receiver2 is equal
        to use the the same receiver
        """
        tip_expiring = yield rtip.get_internaltip_receiver(
            self.receiver1_desc['id'], self.rtip1_id)

        yield rtip.postpone_expiration_date(
                    self.receiver2_desc['id'],
                    self.rtip2_id)

        tip_extended = yield rtip.get_internaltip_receiver(
            self.receiver1_desc['id'], self.rtip1_id)

        self.assertNotEqual(tip_expiring['expiration_date'], tip_extended['expiration_date'])

    @inlineCallbacks
    def postpone_comment_content_check(self):
        """
           'type': "1", # the first kind of structured system_comments
           'receiver_name': rtip.receiver.name,
           'now' : datetime_now(),
           'expire_on' : datetime_to_ISO8601(rtip.internaltip.expiration_date)
        """
        cl = yield rtip.get_comment_list_receiver(self.receiver1_desc['id'],
                                                 self.rtip1_id)

        self.assertEqual(cl[3]['type'], models.Comment._types[2]) # System (date extension)

        sys_comm = cl[3]

        self.assertEqual(sys_comm['system_content']['receiver_name'], self.receiver2_desc['name'])
        # self.assertTrue(sys_comm['system_content'].has_key('now'))
        self.assertEqual(sys_comm['system_content']['type'], u"1")
        new_expire = sys_comm['system_content']['expire_on']

        # TODO implement a more complete test


    @inlineCallbacks
    def receiver2_fail_in_delete_internal_tip(self):
        yield self.assertFailure(rtip.delete_internal_tip(self.receiver2_desc['id'],
                                                          self.rtip2_id),
                                 errors.ForbiddenOperation)

    @inlineCallbacks
    def receiver2_personal_delete(self):
        yield rtip.delete_receiver_tip(self.receiver2_desc['id'], self.rtip2_id)


    @inlineCallbacks
    def receiver1_see_system_comments(self):
        cl = yield rtip.get_comment_list_receiver(self.receiver1_desc['id'],
                                        self.rtip1_id)

        self.assertEqual(len(cl), 5)
        self.assertEqual(cl[0]['type'], models.Comment._types[0]) # Receiver (Rcvr1)
        self.assertEqual(cl[1]['type'], models.Comment._types[0]) # Receiver (Rcvr2)
        self.assertEqual(cl[2]['type'], models.Comment._types[1]) # Wb

        self.assertEqual(cl[3]['type'], models.Comment._types[2]) # System (date extension)
        self.assertEqual(cl[3]['system_content']['receiver_name'], self.receiver2_desc['name'])
        # self.assertTrue(cl[3]['system_content'].has_key('now'))

        self.assertEqual(cl[4]['type'], models.Comment._types[2]) # System


    @inlineCallbacks
    def receiver1_global_delete_tip(self):

        yield rtip.delete_internal_tip(self.receiver1_desc['id'],
            self.rtip1_id)

        try:
            # just one operation that fail if iTip is invalid
            yield rtip.get_internaltip_receiver(
                        self.receiver1_desc['id'], self.rtip1_id)
            self.assertTrue(False)
        except errors.TipIdNotFound:
            self.assertTrue(True)
        except Exception, e:
            self.assertTrue(False)
            raise e


    @inlineCallbacks
    def check_wb_messages_expected(self, expected_msgs):

        x = yield wbtip.get_messages_content(self.wb_tip_id, self.receiver1_desc['id'])
        self.assertEqual(len(x), expected_msgs)

        y = yield wbtip.get_messages_content(self.wb_tip_id, self.receiver2_desc['id'])
        self.assertEqual(len(y), expected_msgs)

    @inlineCallbacks
    def check_receiver_messages_expected(self, expected_msgs):

        x = yield rtip.get_messages_list(self.receiver1_desc['id'], self.rtip1_id)
        self.assertEqual(len(x), expected_msgs)

        y = yield rtip.get_messages_list(self.receiver2_desc['id'], self.rtip2_id)
        self.assertEqual(len(y), expected_msgs)

        # receiver 1 and tip 2 access test
        yield self.assertFailure(rtip.get_messages_list(self.receiver1_desc['id'], self.rtip2_id),
                                 errors.TipIdNotFound)

    @inlineCallbacks
    def do_wb_messages(self):

        before = yield wbtip.get_receiver_list_wb(self.wb_tip_id)


        # the direct message has been sent to the receiver 1, and receiver 1
        # is on the element [0] of the list.
        self.assertEqual(len(before), 2)
        self.assertEqual(before[0]['your_messages'], 0)

        msgrequest = { 'content': u'a msg from wb to receiver1' }
        x = yield wbtip.create_message_wb(self.wb_tip_id,
                                          self.receiver1_desc['id'], msgrequest)

        self.assertEqual(x['author'], u'Whistleblower')

        after = yield wbtip.get_receiver_list_wb(self.wb_tip_id)

        for receivers_message in after:
            if receivers_message['id'] == self.receiver1_desc['id']:
                self.assertEqual(receivers_message['your_messages'], 1)
            else:
                self.assertEqual(receivers_message['your_messages'], 0)

        # and now, two messages for the second receiver
        msgrequest = { 'content': u'#1/2 msg from wb to receiver2' }
        yield wbtip.create_message_wb(self.wb_tip_id,
                                          self.receiver2_desc['id'], msgrequest)
        msgrequest = { 'content': u'#2/2 msg from wb to receiver2' }
        yield wbtip.create_message_wb(self.wb_tip_id,
                                          self.receiver2_desc['id'], msgrequest)

        end = yield wbtip.get_receiver_list_wb(self.wb_tip_id)

        for receivers_message in end:
            if receivers_message['id'] == self.receiver2_desc['id']:
                self.assertEqual(receivers_message['your_messages'], 2)
            else: # the messages from Receiver1 are not changed, right ?
                self.assertEqual(receivers_message['your_messages'], 1)

    @inlineCallbacks
    def do_receivers_messages_and_unread_verification(self):

        # Receiver1 check the presence of the whistleblower message (only 1)
        x = yield receiver.get_receiver_tip_list(self.receiver1_desc['id'])
        self.assertEqual(x[0]['unread_messages'], 1)

        # Receiver1 send one message
        msgrequest = { 'content': u'Receiver1 send a message to WB' }
        k = yield rtip.create_message_receiver(self.receiver1_desc['id'],
                                               self.rtip1_id, msgrequest)
        self.assertEqual(k['visualized'], False)
        self.assertEqual(k['content'], msgrequest['content'])

        # Whistleblower check the presence of receiver1 unread message
        receiver_info_list = yield wbtip.get_receiver_list_wb(self.wb_tip_id)

        for r in receiver_info_list:
            if r['id'] == self.receiver1_desc['id']:
                self.assertEqual(r['name'], self.receiver1_desc['name'])
                self.assertEqual(r['unread_messages'], 1)
                self.assertEqual(r['your_messages'], 1)
            else:
                self.assertEqual(r['name'], self.receiver2_desc['name'])
                self.assertEqual(r['unread_messages'], 0)
                self.assertEqual(r['your_messages'], 2)

        # Receiver2 check the presence of the whistleblower message (2 expected)
        a = yield receiver.get_receiver_tip_list(self.receiver1_desc['id'])
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]['your_messages'], 1)
        self.assertEqual(a[0]['unread_messages'], 1)
        self.assertEqual(a[0]['read_messages'], 0)

        # Receiver2 READ the messages from the whistleblower
        unread = yield rtip.get_messages_list(self.receiver2_desc['id'], self.rtip2_id)
        self.assertEqual(unread[0]['visualized'], unread[1]['visualized'])
        self.assertEqual(unread[0]['visualized'], False)

        readed = yield rtip.get_messages_list(self.receiver2_desc['id'], self.rtip2_id)
        self.assertEqual(readed[0]['visualized'], readed[1]['visualized'])
        self.assertEqual(readed[0]['visualized'], True)

        # Receiver2 send two message
        msgrequest = { 'content': u'Receiver2 send #1/2 message to WB' }
        a1 = yield rtip.create_message_receiver(self.receiver2_desc['id'],
                                                self.rtip2_id, msgrequest)
        msgrequest = { 'content': u'Receiver2 send #2/2 message to WB' }
        a2 = yield rtip.create_message_receiver(self.receiver2_desc['id'],
                                                self.rtip2_id, msgrequest)

        # Whistleblower read the messages from Receiver2
        wunread = yield wbtip.get_messages_content(self.wb_tip_id, self.receiver2_desc['id'])
        self.assertEqual(len(wunread), 4) # two msg from Wb, two from R2
        self.assertFalse(wunread[2]['visualized'])
        self.assertFalse(wunread[3]['visualized'])

        wreaded = yield wbtip.get_messages_content(self.wb_tip_id, self.receiver2_desc['id'])
        self.assertTrue(wreaded[2]['visualized'])
        self.assertTrue(wreaded[3]['visualized'])

        # Whistleblower check 0 unread messages from Receiver2, and still 1 from R1
        end = yield wbtip.get_receiver_list_wb(self.wb_tip_id)
        

        for recv in end:
            if recv['id'] == self.receiver2_desc['id']:
                self.assertEqual(recv['unread_messages'], 0)
            else:
                self.assertEqual(recv['unread_messages'], 1)


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

        # test of direct messages
        yield self.check_wb_messages_expected(0)
        yield self.check_receiver_messages_expected(0)
        yield self.do_wb_messages()
        yield self.do_receivers_messages_and_unread_verification()
        # end direct messages block

        yield self.increment_access_counter()
        # this is the only test on receiver handler and not in tip handler:
        yield self.receiver1_get_tip_list()
        yield self.receiver1_express_positive_vote()
        yield self.receiver2_express_negative_vote()
        yield self.receiver2_fail_double_vote()
        yield self.receiver_2_get_banned_for_too_much_access()
        yield self.receiver_RW_comments()
        yield self.wb_RW_comments()
        yield self.wb_get_receiver_list(GLSetting.memory_copy.default_language)
        yield self.receiver_get_receiver_list(GLSetting.memory_copy.default_language)
        # test expiration date
        yield self.fail_postpone_expiration_date()
        yield self.verify_default_expiration_date()
        yield self.update_node_properties()
        yield self.success_postpone_expiration_date()
        yield self.postpone_comment_content_check()
        # end of test
        yield self.receiver2_fail_in_delete_internal_tip()
        yield self.receiver2_personal_delete()
        yield self.receiver1_see_system_comments()
        yield self.receiver1_global_delete_tip()
