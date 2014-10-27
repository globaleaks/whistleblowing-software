# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.rest.requests import adminContextDesc, adminReceiverDesc
from globaleaks.rest.errors import GLException, InvalidInputFormat
from globaleaks.handlers import base, admin, submission
from globaleaks.tests.test_tip import TTip
from globaleaks.models import Context, Receiver

class MockHandler(base.BaseHandler):

    def __init__(self):
        pass

class SubmissionTest(helpers.TestGL):
    """
    This unitTest want to explore various logic attacks scenario:
    like: https://github.com/globaleaks/GlobaLeaks/issues/31
    """

    context_used = None
    context_unused = None
    receiver_used = None
    receiver_unused = None
    submission_desc = None

    def setUp(self):
        # helpers.TestGL.setUp(self) is done only in the first test
        pass

    def tearDown(self):
        # helpers.TestGL.tearDown(self) is done only in the last test
        pass

    aContext1 = TTip.tipContext

    aContext2 = {
        'name': u'UNUSED', 'description': u'UNUSED',
        'escalation_threshold': u'0', 'tip_max_access': u'2',
        'tip_timetolive': 200, 'file_max_download': 2, 'selectable_receiver': True,
        'receivers': [], 'fields': helpers.default_context_fields(), 'submission_timetolive': 100,
        'file_required': False, 'tags' : [ u'one', u'two', u'y' ],
        'select_all_receivers': True,
        'receiver_introduction': u"bleh",
        'fields_introduction': u"dcsdcsdc¼¼",
        'postpone_superpower': False,
        'can_delete_submission': False,
        'maximum_selectable_receivers': 0,
        'require_file_description': False,
        'delete_consensus_percentage': 0,
        'require_pgp': False,
        'show_small_cards': False,
        'show_receivers': False,
        'enable_private_messages': True,
        'presentation_order': 0,
    }

    aReceiver1 = TTip.tipReceiver1
    aReceiver2 = TTip.tipReceiver2


class TestTipInstance(SubmissionTest):

    @inlineCallbacks
    def test_001_setup_submission_environment(self):
        helpers.TestGL.setUp(self)
        
        basehandler = MockHandler()

        stuff = u"AAA :P ³²¼½¬¼³²"

        for attrname in Context.localized_strings:
            SubmissionTest.aContext1[attrname] = stuff

        basehandler.validate_jmessage( SubmissionTest.aContext1, adminContextDesc)
        SubmissionTest.context_used = yield admin.create_context(SubmissionTest.aContext1)

        # Correctly, TTip.tipContext has not selectable receiver, and we want test it in the 2nd test
        SubmissionTest.context_used['selectable_receiver'] = True

        for attrname in Context.localized_strings:
            SubmissionTest.context_used[attrname] = stuff

        SubmissionTest.context_used = yield admin.update_context(SubmissionTest.context_used['id'],
            SubmissionTest.context_used)

        basehandler.validate_jmessage( SubmissionTest.aContext2, adminContextDesc)
        SubmissionTest.context_unused = yield admin.create_context(SubmissionTest.aContext2)

        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)
        self.assertTrue(len(SubmissionTest.context_unused['id']) > 1)

        SubmissionTest.aReceiver1['contexts'] = [ SubmissionTest.context_used['id'] ]

        for attrname in Receiver.localized_strings:
            SubmissionTest.aReceiver1[attrname] = stuff * 2
            SubmissionTest.aReceiver2[attrname] = stuff * 4

        basehandler.validate_jmessage( SubmissionTest.aReceiver1, adminReceiverDesc )
        SubmissionTest.receiver_used = yield admin.create_receiver(SubmissionTest.aReceiver1)

        SubmissionTest.aReceiver2['contexts'] = [ SubmissionTest.context_unused['id'] ]
        basehandler.validate_jmessage( SubmissionTest.aReceiver2, adminReceiverDesc )
        SubmissionTest.receiver_unused = yield admin.create_receiver(SubmissionTest.aReceiver2)

        self.assertTrue(SubmissionTest.receiver_used['name'] == SubmissionTest.aReceiver1['name'])
        self.assertTrue(SubmissionTest.receiver_unused['name'] == SubmissionTest.aReceiver2['name'])

        self.assertTrue(len(SubmissionTest.receiver_used['contexts']), 1)
        self.assertTrue(len(SubmissionTest.receiver_unused['contexts']), 1)


    @inlineCallbacks
    def test_002_create_submission_missing_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        submission_request = dict( self.get_dummy_submission(SubmissionTest.context_used['id'],
                                                             SubmissionTest.context_used['fields']) )
        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 GLException)


    @inlineCallbacks
    def test_003_create_submission_flip_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        submission_request = dict( self.get_dummy_submission(SubmissionTest.context_used['id'],
                                                             SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['id'] ]
        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 GLException)

    @inlineCallbacks
    def test_004_create_submission_both_valid_and_invalid_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        submission_request = dict( self.get_dummy_submission(SubmissionTest.context_used['id'],
                                                             SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['id'],
                                            SubmissionTest.receiver_used['id']  ]
        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 GLException)


    @inlineCallbacks
    def test_005_create_valid_submission(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        submission_request = dict( self.get_dummy_submission(SubmissionTest.context_used['id'],
                                                             SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_used['id']  ]
        submission_request['finalize'] = True

        yield submission.create_submission(submission_request, finalize=True)

    @inlineCallbacks
    def test_006_fail_create_huge_submission(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        submission_request = dict( self.get_dummy_submission(SubmissionTest.context_used['id'],
                                                             SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_used['id'] ]
        submission_request['context_id'] = SubmissionTest.context_used['id']

        for key in submission_request['wb_fields'].keys():
            submission_request['wb_fields'][key] = { u'value': unicode("You know nothing John Snow" * 100 * 100),
                                                     u'answer_order': 0 }

        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 InvalidInputFormat)
