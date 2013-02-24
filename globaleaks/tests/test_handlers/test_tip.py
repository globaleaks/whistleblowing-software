import re
from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.rest import errors, requests
from globaleaks.handlers import tip, base, admin, submission, authentication

class MockHandler(base.BaseHandler):

    def __init__(self):
        pass

class TTip(helpers.TestHandler):

    context_desc = None
    receiver1_desc = receiver2_desc = None
    submission_desc = None
    receipt = None

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
        'receiver_level': u'2', 'can_delete_submission': False,
        'password': u'x'
    }

    tipSubmission = {
        'wb_fields': {'headline': u'an headline', 'Sun': u'a Sun'},
        'context_gus': '', 'receivers': [], 'files': [], 'finalize': True
    }


class TestTipInstance(TTip):
    _handler = tip.TipInstance

    # Test model is required *before*, for create e valid environment where Tip lives

    # The test environment has one context (escalation 1, tip TTL 2, max file download 1)
    #                          two receiver ("first" level 1, "second" level 2)
    # Test context would just contain two receiver, one level 1 and the other level 2

    # They are defined in:
    # helpers.tipContext helpers.tipReceiver1 helpers.tipReceiver2 helpers.tipSubmission

    @inlineCallbacks
    def test_1_setup_tip_environment(self):

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

        print TTip.submission_desc

        self.assertEqual(TTip.submission_desc['wb_fields'], TTip.tipSubmission['wb_fields'])
        # Ok, now the submission has been finalized, the tests can start.

    @inlineCallbacks
    def test_wb_interactions(self):
        """
        emulate auth, get wb_tip.id, get the data like GET /tip/xxx
        """

        if not TTip.receipt:
            TTip.receipt = yield submission.create_whistleblower_tip(TTip.submission_desc)
            self.assertTrue(re.match('(\w+){10}', TTip.receipt) )

        wb_tip_id = yield authentication.login_wb(TTip.receipt)
        # is the self.current_user['user_id']

        (answer, internaltip_id) = yield tip.get_internaltip_wb(wb_tip_id)
        print self.submission_desc, internaltip_id
        print answer
        self.assertEqual(internaltip_id, TTip.submission_desc['submission_gus'])



    @inlineCallbacks
    def test_put_whistleblower_tip_fails(self):
        tip_id = self.dummySubmission['context_gus']
        
        handler = self.request()
        handler.request.headers['X-Session'] = self.login()
        d = yield handler.put(tip_id)
        self.assertFailure(d, errors.ForbiddenOperation)

    @inlineCallbacks
    def test_delete_receiver_tip(self):
        tip_id = self.dummySubmission['context_gus']
        self.dummySubmission['context_gus'] = {'spam': u'ham'}

        handler = self.request()
        handler.request.headers['X-Session'] = self.login('receiver')

        yield handler.delete(tip_id)

    @inlineCallbacks
    def test_put_global_delete_receiver_tip(self):
        req = {
            'total_delete': True,
            'is_pertinent': False
        }
        tip_id = self.dummySubmission['context_gus']
        self.dummySubmission['context_gus'] = {'spam': u'ham'}

        handler = self.request(req)
        handler.request.headers['X-Session'] = self.login('receiver')

        yield handler.put(tip_id)


    class TestTipCommentCollection(helpers.TestHandler):
        _handler = tip.TipCommentCollection

        def test_get(self):
            handler = self.request({})
            return handler.get()

        def test_put(self):
            handler = self.request({})
            return handler.get()

    class TestTipReceiversCollection(helpers.TestHandler):
        _handler = tip.TipReceiversCollection

        def test_get(self):
            handler = self.request({})
            return handler.get()

        def test_post(self):
            pass


