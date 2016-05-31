from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import authentication, admin
from globaleaks.handlers.base import BaseHandler, GLSessions, GLSession
from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.utils import utility
from globaleaks.security import derive_auth_hash


class TestAuthentication(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.AuthenticationHandler

    # Since all logins for roles admin, receiver and custodian work the 
    # same way, the following tests are performed on the admin user.

    @inlineCallbacks
    def _test_successful_login(self, headers={}):
        uname = 'receiver1@receiver1.xxx'
        handler = self.request({
            'step': 1,
            'username': uname,
            'auth_token_hash': 'f'*128,
        }, headers=headers)
        yield handler.post()

        salt = self.responses[0]['salt']

        password = helpers.VALID_PASSWORD1
        digest = derive_auth_hash(password, salt)

        handler = self.request({
            'step': 2,
            'username': uname,
            'auth_token_hash': helpers.VALID_AUTH_TOK_HASH1,
        }, headers=headers)

        success = yield handler.post()

        self.assertTrue('session_id' in self.responses[1])
          
        self.assertEqual(len(GLSessions.keys()), 1)

    @inlineCallbacks
    def test_successful_login(self):
      yield self._test_successful_login()

    @inlineCallbacks
    def test_accept_login_in_tor2web(self):
        GLSettings.memory_copy.accept_tor2web_access['admin'] = True
        yield self._test_successful_login({'X-Tor2Web': 'whatever'})

    @inlineCallbacks
    def test_deny_login_in_tor2web(self):
        GLSettings.memory_copy.accept_tor2web_access['admin'] = False
        yield self.assertFailure(self._test_successful_login({'X-Tor2Web': 'whatever'}), 
                                 errors.TorNetworkRequired)

    @inlineCallbacks
    def test_successful_logout(self):
        # Login
        yield self._test_successful_login()

        # Logout
        session_id = self.responses[1]['session_id']
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
    def test_invalid_login_wrong_token(self):
        handler = self.request({
            'username': 'admin',
            'auth_token_hash': helpers.INVALID_AUTH_TOK_HASH,
            'step': 2,
        })

        yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

    @inlineCallbacks
    def test_failed_login_counter(self):
        handler = self.request({
            'username': 'admin',
            'auth_token_hash': helpers.INVALID_AUTH_TOK_HASH,
            'step': 2,
        })

        failed_login = 5
        for i in xrange(0, failed_login):
            yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

        receiver_status = yield admin.receiver.get_receiver(self.dummyReceiver_1['id'], 'en')
        self.assertEqual(GLSettings.failed_login_attempts, failed_login)


class TestReceiptAuth(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.ReceiptAuthHandler

    @inlineCallbacks
    def test_invalid_whistleblower_login(self):
        handler = self.request({
            'receipt_hash': helpers.RECEIPT_HASH
        })

        yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

    @inlineCallbacks
    def test_successful_whistleblower_login(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt_hash': helpers.RECEIPT_HASH
        })
        yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

    @inlineCallbacks
    def test_accept_whistleblower_login_in_tor2web(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt_hash': helpers.RECEIPT_HASH
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.accept_tor2web_access['whistleblower'] = True
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSessions.keys()), 1)

    @inlineCallbacks
    def test_deny_whistleblower_login_in_tor2web(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt_hash': helpers.RECEIPT_HASH
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.accept_tor2web_access['whistleblower'] = False
        yield self.assertFailure(handler.post(), errors.TorNetworkRequired)

    @inlineCallbacks
    def test_successful_whistleblower_logout(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt_hash': helpers.RECEIPT_HASH
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
        self.assertEqual(len(GLSeessions.keys()), 0)

        # A second logout must not be accepted (this validate also X-Session reuse)
        handler = self.request({}, headers={'X-Session': session_id})

        self.assertRaises(errors.NotAuthenticated, handler.delete)

        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSessions.keys()), 0)

    @inlineCallbacks
    def test_successful_whistleblower_logout(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt_hash': helpers.RECEIPT_HASH
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
