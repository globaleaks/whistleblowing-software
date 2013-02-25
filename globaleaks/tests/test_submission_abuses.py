import re

from storm.twisted.testing import FakeThreadPool
from twisted.internet.defer import inlineCallbacks
from twisted.trial import unittest

from globaleaks.rest import errors, requests
from globaleaks.rest.errors import GLException
from globaleaks.rest.base import uuid_regexp
from globaleaks.handlers import tip, base, admin, submission, authentication
from globaleaks.jobs import delivery_sched
from globaleaks import models, db, settings
from globaleaks.utils import log

_TEST_DB = 'submissionabuse.db'
settings.transact.tp = FakeThreadPool()
settings.scheduler_threadpool = FakeThreadPool()
settings.db_file = 'sqlite:///' + _TEST_DB
settings.store = 'test_store'
settings.notification_plugins = []

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
        'wb_fields': {'headline': u'an headline', 'Sun': u'a Sun'},
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


