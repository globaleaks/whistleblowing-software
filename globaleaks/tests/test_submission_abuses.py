import os

from storm.twisted.testing import FakeThreadPool
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

# Override the GLSetting with test values
from globaleaks.settings import GLSetting, transact
from globaleaks.tests import helpers

from globaleaks.rest import requests
from globaleaks.rest.errors import GLException, InvalidInputFormat
from globaleaks.handlers import base, admin, submission
from globaleaks import db
from globaleaks.utils import log

class MockHandler(base.BaseHandler):

    def __init__(self):
        pass

class SubmissionTest(unittest.TestCase):
    """
    This unitTest want to explore various logic attacks scenario:
    like: https://github.com/globaleaks/GlobaLeaks/issues/31
    """

    context_used = context_unused = None
    receiver_used = receiver_unused = None
    submission_desc = None

    @inlineCallbacks
    def initalize_db(self):
        try:
            yield db.createTables(create_node=True)
        except Exception, e:
            print "Fatal: unable to createTables [%s]" % str(e)
            raise e

    aContext1 = {
        'name': u'CtxName', 'description': u'dummy context with default fields',
        'escalation_threshold': u'0', 'tip_max_access': u'2',
        'tip_timetolive': 1, 'file_max_download': 2, 'selectable_receiver': True,
        'receivers': [], 'fields': []
    }

    aContext2 = {
        'name': u'UNUSED', 'description': u'UNUSED',
        'escalation_threshold': u'0', 'tip_max_access': u'2',
        'tip_timetolive': 1, 'file_max_download': 2, 'selectable_receiver': True,
        'receivers': [], 'fields': []
    }

    aReceiver1 = {
        'name': u'first', 'description': u"I'm tha 1st",
        'notification_fields': {'mail_address': u'first@winstonsmith.org' },
        'receiver_level': 1, 'can_delete_submission': False, 'password': u'x',
    }

    aReceiver2 = {
        'name': u'UNUSED', 'description': u"UNUSED",
        'notification_fields': {'mail_address': u'unused@winstonsmith.org' },
        'receiver_level': 1, 'can_delete_submission': False, 'password': u'x',
    }

    aSubmission = {
        'wb_fields': {'headline': u'an headline', 'description': u'a dummy deskription'},
        'context_gus': '', 'receivers': [], 'files': [], 'finalize': False
    }


class TestTipInstance(SubmissionTest):

    @inlineCallbacks
    def test_1_setup_submission_environment(self):

        self.initalize_db()
        basehandler = MockHandler()

        basehandler.validate_jmessage( SubmissionTest.aContext1, requests.adminContextDesc)
        SubmissionTest.context_used = yield admin.create_context(SubmissionTest.aContext1)

        basehandler.validate_jmessage( SubmissionTest.aContext2, requests.adminContextDesc)
        SubmissionTest.context_unused = yield admin.create_context(SubmissionTest.aContext2)

        SubmissionTest.aReceiver1['contexts'] = [ SubmissionTest.context_used['context_gus'] ]
        basehandler.validate_jmessage( SubmissionTest.aReceiver1, requests.adminReceiverDesc )
        SubmissionTest.receiver_used = yield admin.create_receiver(SubmissionTest.aReceiver1)

        SubmissionTest.aReceiver2['contexts'] = [ SubmissionTest.context_unused['context_gus'] ]
        basehandler.validate_jmessage( SubmissionTest.aReceiver2, requests.adminReceiverDesc )
        SubmissionTest.receiver_unused = yield admin.create_receiver(SubmissionTest.aReceiver2)

        self.assertTrue(SubmissionTest.receiver_used['name'] == SubmissionTest.aReceiver1['name'])
        self.assertTrue(SubmissionTest.receiver_unused['name'] == SubmissionTest.aReceiver2['name'])

        self.assertTrue(len(SubmissionTest.receiver_used['contexts']), 1)
        self.assertTrue(len(SubmissionTest.receiver_unused['contexts']), 1)


    @inlineCallbacks
    def test_2_create_submission_missing_receiver(self):
        submission_request = dict(SubmissionTest.aSubmission)

        submission_request['receivers'] = []
        submission_request['context_gus'] = SubmissionTest.context_used['context_gus']
        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            log.debug("Success in creation: %s" % str(r))
            self.assertTrue(False)
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertEqual(e.error_code, 22) # SubmissionFailFields
        except Exception, e:
            log.debug("Exception %s" % str(e) )
            self.assertTrue(False, msg=str(e))


    @inlineCallbacks
    def test_3_create_submission_flip_receiver(self):
        submission_request = dict(SubmissionTest.aSubmission)

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['receiver_gus'] ]
        submission_request['context_gus'] = SubmissionTest.context_used['context_gus']
        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            log.debug("Success in creation: %s" % str(r))
            self.assertTrue(False)
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertTrue(True)
        except Exception, e:
            log.debug("Exception %s" % str(e) )
            self.assertTrue(False, msg=str(e))


    @inlineCallbacks
    def test_4_create_submission_both_valid_and_invalid_receiver(self):
        submission_request = dict(SubmissionTest.aSubmission)

        submission_request['receivers'] = [ SubmissionTest.receiver_unused['receiver_gus'],
                                            SubmissionTest.receiver_used['receiver_gus']  ]
        submission_request['context_gus'] = SubmissionTest.context_used['context_gus']
        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            log.debug("Success in creation: %s" % str(r))
            self.assertTrue(False, msg="Created!")
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertTrue(True)
        except Exception, e:
            log.debug("Exception %s" % str(e) )
            self.assertTrue(False, msg=str(e))


    @inlineCallbacks
    def test_5_create_valid_submission(self):
        submission_request = dict(SubmissionTest.aSubmission)

        submission_request['receivers'] = [ SubmissionTest.receiver_used['receiver_gus']  ]
        submission_request['context_gus'] = SubmissionTest.context_used['context_gus']
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
    def test_5_fail_create_huge_submission(self):
        submission_request = dict(SubmissionTest.aSubmission)

        submission_request['receivers'] = [ SubmissionTest.receiver_used['receiver_gus']  ]
        submission_request['context_gus'] = SubmissionTest.context_used['context_gus']
        submission_request['wb_fields']['headline'] = unicode("A" * 1000 * 1000)
        submission_request['wb_fields']['description'] = u'dummy'

        submission_request['finalize'] = True

        try:
            r = yield submission.create_submission(submission_request, finalize=True)
            self.assertTrue(False)
        except InvalidInputFormat:
            self.assertTrue(True)
        except GLException, e:
            log.debug("GLException %s %s" % (str(e), e.reason) )
            self.assertTrue(False)

        os.unlink(helpers._TEST_DB)


