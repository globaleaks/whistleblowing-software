from twisted.internet.defer import inlineCallbacks

from globaleaks.tests import helpers
from globaleaks.handlers import authentication, admin, base
from globaleaks.rest import errors
from globaleaks.settings import GLSettings
from globaleaks.utils import utility

FUTURE = 100

class ClassToTestUnauthenticatedDecorator(base.BaseHandler):
    @authentication.unauthenticated
    def get(self):
        self.set_status(200)
        self.finish("test")


class ClassToTestAuthenticatedDecorator(base.BaseHandler):
    @authentication.authenticated('admin')
    def get(self):
        self.set_status(200)
        self.finish("test")


class TestSessionUpdateOnUnauthRequests(helpers.TestHandlerWithPopulatedDB):
    _handler = ClassToTestUnauthenticatedDecorator

    @inlineCallbacks
    def test_successful_session_update_on_unauth_request(self):
        session = authentication.GLSession('admin', 'admin', 'enabled')
        date1 = session.getTime()
        self.test_reactor.pump([1] * FUTURE)
        handler = self.request({}, headers={'X-Session': session.id})
        yield handler.get()
        date2 = GLSettings.sessions.get(session.id).getTime()
        self.assertEqual(date1 + FUTURE, date2)


class TestSessionUpdateOnAuthRequests(helpers.TestHandlerWithPopulatedDB):
    _handler = ClassToTestAuthenticatedDecorator

    @inlineCallbacks
    def test_successful_session_update_on_auth_request(self):
        session = authentication.GLSession('admin', 'admin', 'enabled')
        date1 = session.getTime()
        self.test_reactor.pump([1] * FUTURE)
        handler = self.request({}, headers={'X-Session': session.id})
        yield handler.get()
        date2 = GLSettings.sessions.get(session.id).getTime()
        self.assertEqual(date1 + FUTURE, date2)


class TestAuthentication(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.AuthenticationHandler

    # since all logins for roles admin, receiver and custodian happen
    # in the same way, the following tests are performed on the admin user.

    @inlineCallbacks
    def test_successful_login(self):
        handler = self.request({
            'username': 'admin',
            'password': 'globaleaks',
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSettings.sessions.keys()), 1)

    @inlineCallbacks
    def test_accept_login_in_tor2web(self):
        handler = self.request({
            'username': 'admin',
            'password': 'globaleaks'
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.tor2web_access['admin'] = True
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSettings.sessions.keys()), 1)

    def test_deny_login_in_tor2web(self):
        handler = self.request({
            'username': 'admin',
            'password': 'globaleaks'
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.tor2web_access['admin'] = False
        self.assertFailure(handler.post(), errors.TorNetworkRequired)

    @inlineCallbacks
    def test_successful_logout(self):
        # Login
        handler = self.request({
            'username': 'admin',
            'password': 'globaleaks'
        })
        yield handler.post()
        self.assertTrue(handler.current_user is None)
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSettings.sessions.keys()), 1)

        # Logout
        session_id = self.responses[0]['session_id']
        handler = self.request({}, headers={'X-Session': session_id})
        yield handler.delete()
        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSettings.sessions.keys()), 0)

        # A second logout must not be accepted (this validate also X-Session reuse)
        handler = self.request({}, headers={'X-Session': session_id})

        self.assertRaises(errors.NotAuthenticated, handler.delete)

        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSettings.sessions.keys()), 0)

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
        for i in xrange(0, failed_login):
            yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

        receiver_status = yield admin.receiver.get_receiver(self.dummyReceiver_1['id'], 'en')
        self.assertEqual(GLSettings.failed_login_attempts, failed_login)

    @inlineCallbacks
    def test_bruteforce_login_protection(self):
        handler = self.request({
            'username': 'admin',
            'password': 'INVALIDPASSWORD'
        })

        sleep_list = []

        def fake_deferred_sleep(seconds):
            sleep_list.append(seconds)

        utility.deferred_sleep = fake_deferred_sleep

        failed_login = 7
        for i in xrange(0, failed_login):
            yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

        receiver_status = yield admin.receiver.get_receiver(self.dummyReceiver_1['id'], 'en')

        self.assertEqual(GLSettings.failed_login_attempts, failed_login)

        # validate incremental delay
        self.assertTrue(len(sleep_list), failed_login)
        for i in xrange(1, len(sleep_list)):
            self.assertTrue(i <= sleep_list[i])


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
        self.assertEqual(len(GLSettings.sessions.keys()), 1)

    @inlineCallbacks
    def test_accept_whistleblower_login_in_tor2web(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.tor2web_access['whistleblower'] = True
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSettings.sessions.keys()), 1)

    @inlineCallbacks
    def test_deny_whistleblower_login_in_tor2web(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        }, headers={'X-Tor2Web': 'whatever'})
        GLSettings.memory_copy.tor2web_access['whistleblower'] = False
        self.assertFailure(handler.post(), errors.TorNetworkRequired)

    @inlineCallbacks
    def test_successful_whistleblower_logout(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        })
        yield handler.post()
        self.assertTrue(handler.current_user is None)
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSettings.sessions.keys()), 1)

        # Logout
        session_id = self.responses[0]['session_id']
        handler = self.request({}, headers={'X-Session': session_id})
        yield handler.delete()
        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSettings.sessions.keys()), 0)

        # A second logout must not be accepted (this validate also X-Session reuse)
        handler = self.request({}, headers={'X-Session': session_id})

        self.assertRaises(errors.NotAuthenticated, handler.delete)

        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSettings.sessions.keys()), 0)

    @inlineCallbacks
    def test_successful_whistleblower_logout(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.dummySubmission['receipt']
        })
        yield handler.post()
        self.assertTrue(handler.current_user is None)
        self.assertTrue('session_id' in self.responses[0])
        self.assertEqual(len(GLSettings.sessions.keys()), 1)

        # Logout
        session_id = self.responses[0]['session_id']
        handler = self.request({}, headers={'X-Session': session_id})
        yield handler.delete()
        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSettings.sessions.keys()), 0)

        # A second logout must not be accepted (this validate also X-Session reuse)
        handler = self.request({}, headers={'X-Session': session_id})

        self.assertRaises(errors.NotAuthenticated, handler.delete)

        self.assertTrue(handler.current_user is None)
        self.assertEqual(len(GLSettings.sessions.keys()), 0)
