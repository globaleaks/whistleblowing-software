from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import authentication, admin
from globaleaks.handlers.base import GLSessions
from globaleaks.handlers.user import UserInstance
from globaleaks.handlers.wbtip import WBTipInstance
from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.tests import helpers


class TestAuthentication(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.AuthenticationHandler

    # since all logins for roles admin, receiver and custodian happen
    # in the same way, the following tests are performed on the admin user.

    @inlineCallbacks
    def test_successful_login(self):
        handler = self.request({
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

    @inlineCallbacks
    def test_accept_login_in_tor2web(self):
        handler = self.request({
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.accept_tor2web_access['admin'] = True
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

    @inlineCallbacks
    def test_deny_login_in_tor2web(self):
        handler = self.request({
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.accept_tor2web_access['admin'] = False
        yield self.assertFailure(handler.post(), errors.TorNetworkRequired)

    @inlineCallbacks
    def test_successful_logout(self):
        # Login
        handler = self.request({
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1
        })
        yield handler.post()
        self.assertTrue(handler.current_user is None)
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

        # Logout
        session_id = self.responses[0]['session_id']
        handler = self.request({}, headers={'X-Session': session_id})
        yield handler.delete()
        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSessions.keys()), 0)

        # A second logout must not be accepted (this validate also X-Session reuse)
        handler = self.request({}, headers={'X-Session': session_id})

        self.assertRaises(errors.NotAuthenticated, handler.delete)

        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSessions.keys()), 0)

    @inlineCallbacks
    def test_invalid_login_wrong_password(self):
        handler = self.request({
            'username': 'admin',
            'password': 'INVALIDPASSWORD'
        })

        yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

    @inlineCallbacks
    def test_failed_login_counter(self):
        handler = self.request({
            'username': 'admin',
            'password': 'INVALIDPASSWORD'
        })

        failed_login = 5
        for _ in xrange(0, failed_login):
            yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

        receiver_status = yield admin.receiver.get_receiver(self.dummyReceiver_1['id'], 'en')
        self.assertEqual(GLSettings.failed_login_attempts, failed_login)

    @inlineCallbacks
    def test_single_session_per_user(self):
        handler = self.request({
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1
        })
        yield handler.post()
        yield handler.post()
        first_id = self.responses[0]['session_id']
        second_id = self.responses[1]['session_id']

        self.assertTrue(GLSessions.get(first_id) is None)

        valid_session = GLSessions.get(second_id)
        self.assertTrue(valid_session is not None)

        self.assertEqual(valid_session.user_role, 'admin')

    @inlineCallbacks
    def test_session_is_revoked(self):
        auth_handler = self.request({
            'username': 'receiver1',
            'password': helpers.VALID_PASSWORD1
        })
        yield auth_handler.post()

        first_session_id = self.responses[0]['session_id']

        user_handler = self.request({}, headers={'X-Session': first_session_id},
                                        handler_cls=UserInstance)
        # The first_session is valid and the request should work
        yield user_handler.get()

        # The second authentication invalidates the first session
        yield auth_handler.post()
        second_session_id = self.responses[2]['session_id']

        # The first_session should now deny access to authenticated resources
        try:
            yield user_handler.get()
            # cannot use self.assertFailure here because self points else where
            self.fail('user_handler.get must throw')
        except errors.NotAuthenticated:
            pass

        # The second_session should have no problems.
        user_handler = self.request({}, headers={'X-Session': second_session_id},
                                        handler_cls=UserInstance)

        yield user_handler.get()

class TestReceiptAuth(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.ReceiptAuthHandler

    @inlineCallbacks
    def test_invalid_whistleblower_login(self):
        handler = self.request({
            'receipt': 'INVALIDRECEIPT'
        })

        yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

    @inlineCallbacks
    def test_successful_whistleblower_login(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        })
        yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

    @inlineCallbacks
    def test_accept_whistleblower_login_in_tor2web(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.accept_tor2web_access['whistleblower'] = True
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

    @inlineCallbacks
    def test_deny_whistleblower_login_in_tor2web(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.accept_tor2web_access['whistleblower'] = False
        yield self.assertFailure(handler.post(), errors.TorNetworkRequired)

    @inlineCallbacks
    def test_successful_whistleblower_logout(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        })
        yield handler.post()
        self.assertTrue(handler.current_user is None)
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

        # Logout
        session_id = self.responses[0]['session_id']
        handler = self.request({}, headers={'X-Session': session_id})
        yield handler.delete()
        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSessions.keys()), 0)

        # A second logout must not be accepted (this validate also X-Session reuse)
        handler = self.request({}, headers={'X-Session': session_id})

        self.assertRaises(errors.NotAuthenticated, handler.delete)

        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSessions.keys()), 0)

    @inlineCallbacks
    def test_single_session_per_whistleblower(self):
        '''Asserts that the first_id is dropped from GLSessions and requests
        using that session id are rejected'''
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        })
        yield handler.post()

        first_id = self.responses[0]['session_id']
        wbtip_handler = self.request(headers={'X-Session': first_id},
                                     handler_cls=WBTipInstance)
        yield wbtip_handler.get()

        yield handler.post()
        second_id = self.responses[2]['session_id']

        try:
            wbtip_handler.get()
            self.fail('wbtip_handler.get must throw')
        except errors.NotAuthenticated:
            pass

        self.assertTrue(GLSessions.get(first_id) is None)

        valid_session = GLSessions.get(second_id)
        self.assertTrue(valid_session is not None)

        self.assertEqual(valid_session.user_role, 'whistleblower')

        wbtip_handler = self.request(headers={'X-Session': second_id},
                                     handler_cls=WBTipInstance)
        yield wbtip_handler.get()
