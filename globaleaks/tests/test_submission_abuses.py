# -*- coding: UTF-8

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import sample_context_fields
from globaleaks.tests import helpers
from globaleaks.rest.requests import adminContextDesc, adminReceiverDesc
from globaleaks.rest.errors import GLException, InvalidInputFormat
from globaleaks.handlers import base, admin, submission
from globaleaks.utils.utility import log
from globaleaks.tests.test_tip import TTip

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
        'receivers': [], 'fields': sample_context_fields, 'submission_timetolive': 100,
        'receipt_regexp': u"[0-9]{10}",
        'receipt_description': u"blah",
        'submission_introduction': u"bleh",
        'submission_disclaimer': u"bloh",
        'file_required': False, 'tags' : [ u'one', u'two', u'y' ],
        'select_all_receivers': True,
    }

    aReceiver1 = TTip.tipReceiver1
    aReceiver2 = TTip.tipReceiver2


class TestTipInstance(SubmissionTest):

    @inlineCallbacks
    def test_1_setup_submission_environment(self):
        helpers.TestGL.setUp(self)
        
        basehandler = MockHandler()

        # context creation
        try:
            basehandler.validate_jmessage( SubmissionTest.aContext1, adminContextDesc)
            SubmissionTest.context_used = yield admin.create_context(SubmissionTest.aContext1)
            # Correctly, TTip.tipContext has not selectable receiver, and we want test it in the 2nd test
            SubmissionTest.context_used['selectable_receiver'] = True
            SubmissionTest.context_used = yield admin.update_context(SubmissionTest.context_used['context_gus'],
                SubmissionTest.context_used)
            basehandler.validate_jmessage( SubmissionTest.aContext2, adminContextDesc)
            SubmissionTest.context_unused = yield admin.create_context(SubmissionTest.aContext2)
        except Exception as excep:
            log.err("Unable to create context used/unused in UT: %s" % excep.message)
            raise excep

        self.assertTrue(len(SubmissionTest.context_used['context_gus']) > 1)
        self.assertTrue(len(SubmissionTest.context_unused['context_gus']) > 1)

        SubmissionTest.aReceiver1['contexts'] = [ SubmissionTest.context_used['context_gus'] ]
        basehandler.validate_jmessage( SubmissionTest.aReceiver1, adminReceiverDesc )
        SubmissionTest.receiver_used = yield admin.create_receiver(SubmissionTest.aReceiver1)

        SubmissionTest.aReceiver2['contexts'] = [ SubmissionTest.context_unused['context_gus'] ]
        basehandler.validate_jmessage( SubmissionTest.aReceiver2, adminReceiverDesc )
        SubmissionTest.receiver_unused = yield admin.create_receiver(SubmissionTest.aReceiver2)

        self.assertTrue(SubmissionTest.receiver_used['name'] == SubmissionTest.aReceiver1['name'])
        self.assertTrue(SubmissionTest.receiver_unused['name'] == SubmissionTest.aReceiver2['name'])

        self.assertTrue(len(SubmissionTest.receiver_used['contexts']), 1)
        self.assertTrue(len(SubmissionTest.receiver_unused['contexts']), 1)


    @inlineCallbacks
    def test_2_create_submission_missing_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['context_gus']) > 1)

        submission_request = dict( helpers.get_dummy_submission(SubmissionTest.context_used['context_gus'],
                                                                SubmissionTest.context_used['fields']) )
        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            log.debug("Unexpected Success in creation: %s" % str(r))
            self.assertTrue(False)
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.message) )
            self.assertEqual(e.error_code, 22) # SubmissionFailFields
        except Exception, e:
            log.debug("Unexpected Exception %s" % str(e.message) )
            self.assertTrue(False, msg=str(e.message))


    @inlineCallbacks
    def test_3_create_submission_flip_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['context_gus']) > 1)

        submission_request = dict( helpers.get_dummy_submission(SubmissionTest.context_used['context_gus'],
                                                                SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['receiver_gus'] ]
        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            log.debug("Unexpected Success in creation: %s" % str(r))
            self.assertTrue(False)
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertTrue(True)
        except Exception, e:
            log.debug("Unexpected Exception %s" % str(e) )
            self.assertTrue(False, msg=str(e))


    @inlineCallbacks
    def test_4_create_submission_both_valid_and_invalid_receiver(self):
        self.assertTrue(len(SubmissionTest.context_used['context_gus']) > 1)

        submission_request = dict( helpers.get_dummy_submission(SubmissionTest.context_used['context_gus'],
                                                                SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['receiver_gus'],
                                            SubmissionTest.receiver_used['receiver_gus']  ]
        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            log.debug("Unexpected Success in creation: %s" % str(r))
            self.assertTrue(False, msg="Created!")
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertTrue(True)
        except Exception, e:
            log.debug("Unexpected Exception %s" % str(e) )
            self.assertTrue(False, msg=str(e))


    @inlineCallbacks
    def test_5_create_valid_submission(self):
        self.assertTrue(len(SubmissionTest.context_used['context_gus']) > 1)

        submission_request = dict( helpers.get_dummy_submission(SubmissionTest.context_used['context_gus'],
                                                                SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_used['receiver_gus']  ]
        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            log.debug("Success in creation: %s" % str(r))
            self.assertTrue(True)
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertTrue(False)
        except Exception, e:
            log.debug("Exception %s" % str(e) )
            self.assertTrue(False, msg=str(e))


    @inlineCallbacks
    def test_6_fail_create_huge_submission(self):
        self.assertTrue(len(SubmissionTest.context_used['context_gus']) > 1)

        submission_request = dict( helpers.get_dummy_submission(SubmissionTest.context_used['context_gus'],
                                                                SubmissionTest.context_used['fields']) )

        submission_request['receivers'] = [ SubmissionTest.receiver_used['receiver_gus'] ]
        submission_request['context_gus'] = SubmissionTest.context_used['context_gus']

        for key in submission_request['wb_fields'].keys():
            submission_request['wb_fields'][key] = unicode("You know nothing John Snow" * 100 * 100)

        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            self.assertTrue(False)
        except InvalidInputFormat:
            self.assertTrue(True)
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertTrue(False)

        helpers.TestGL.tearDown(self)


