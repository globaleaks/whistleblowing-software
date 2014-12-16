# -*- encoding: utf-8 -*-

import copy

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

    aContext1 = copy.deepcopy(TTip.tipContext)

    aContext2 = {
        'name': u'UNUSED', 'description': u'UNUSED',
        'escalation_threshold': u'0', 'tip_max_access': u'2',
        'tip_timetolive': 200,
        'file_max_download': 2,
        'selectable_receiver': True,
        'receivers': [],
        'submission_timetolive': 100,
        'tags' : [ u'one', u'two', u'y' ],
        'select_all_receivers': True,
        'receiver_introduction': u"bleh",
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
        'steps': []
    }

    aReceiver1 = copy.deepcopy(TTip.tipReceiver1)
    aReceiver2 = copy.deepcopy(TTip.tipReceiver2)


class TestTipInstance(SubmissionTest):

    @inlineCallbacks
    def test_001_setup_submission_environment(self):
        helpers.TestGL.setUp(self)
        
        basehandler = MockHandler()

        stuff = u"AAA :P ³²¼½¬¼³²"

        for attrname in Context.localized_strings:
            SubmissionTest.aContext1[attrname] = stuff

        basehandler.validate_jmessage(SubmissionTest.aContext1, adminContextDesc)

        # the test context need fields to be present
        from globaleaks.handlers.admin.field import create_field
        for idx, field in enumerate(self.dummyFields):
            f = yield create_field(field, 'en')
            self.dummyFields[idx]['id'] = f['id']

        SubmissionTest.aContext1['steps'][0]['children'] = [
            self.dummyFields[0], # Field 1
            self.dummyFields[1], # Field 2
            self.dummyFields[4]  # Generalities
        ]

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

        fields = yield admin.get_context_fields(SubmissionTest.context_used['id'])
        submission_request = yield self.get_dummy_submission(SubmissionTest.context_used['id'])
        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 GLException)


    @inlineCallbacks
    def test_003_create_submission_flip_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        fields = yield admin.get_context_fields(SubmissionTest.context_used['id'])
        submission_request = yield self.get_dummy_submission(SubmissionTest.context_used['id'])

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['id'] ]
        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 GLException)

    @inlineCallbacks
    def test_004_create_submission_both_valid_and_invalid_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        fields = yield admin.get_context_fields(SubmissionTest.context_used['id'])
	submission_request = yield self.get_dummy_submission(SubmissionTest.context_used['id'])

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['id'],
                                            SubmissionTest.receiver_used['id']  ]
        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 GLException)


    @inlineCallbacks
    def test_005_create_valid_submission(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        fields = yield admin.get_context_fields(SubmissionTest.context_used['id'])
        submission_request = yield self.get_dummy_submission(SubmissionTest.context_used['id'])

        submission_request['receivers'] = [ SubmissionTest.receiver_used['id']  ]
        submission_request['finalize'] = True

        yield submission.create_submission(submission_request, finalize=True)

    @inlineCallbacks
    def test_006_fail_create_huge_submission(self):
        self.assertTrue(len(SubmissionTest.context_used['id']) > 1)

        fields = yield admin.get_context_fields(SubmissionTest.context_used['id'])
        submission_request = yield self.get_dummy_submission(SubmissionTest.context_used['id'])

        submission_request['receivers'] = [ SubmissionTest.receiver_used['id'] ]
        submission_request['context_id'] = SubmissionTest.context_used['id']

        for wb_step in submission_request['wb_steps']:
            for c in wb_step['children']:
                c['value'] = unicode("You know nothing John Snow" * 100  * 100)

        submission_request['finalize'] = True

        yield self.assertFailure(submission.create_submission(submission_request, finalize=True),
                                 InvalidInputFormat)
