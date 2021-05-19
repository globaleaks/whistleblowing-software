# -*- coding: utf-8 -*-
from twisted.internet.address import IPv4Address
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import authentication
from globaleaks.handlers.user import UserInstance
from globaleaks.handlers.wbtip import WBTipInstance
from globaleaks.rest import errors
from globaleaks.sessions import Sessions
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.tests import helpers


class TestAuthentication(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.AuthenticationHandler

    # since all logins for roles admin, receiver and custodian happen
    # in the same way, the following tests are performed on the admin user.

    @inlineCallbacks
    def test_successful_login(self):
        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': '',
        })
        response = yield handler.post()
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)

    @inlineCallbacks
    def test_successful_multitenant_login_switch(self):
        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': ''
        })

        response = yield handler.post()

        auth_switch_handler = self.request({},
                                           headers={'x-session': response['session_id']},
                                           handler_cls=authentication.TenantAuthSwitchHandler)

        response = yield auth_switch_handler.get(2)
        self.assertTrue('redirect' in response)

    @inlineCallbacks
    def test_accept_login_in_https(self):
        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': ''
        })
        State.tenant_cache[1]['https_allowed']['admin'] = True
        response = yield handler.post()
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)

    @inlineCallbacks
    def test_deny_login_in_https(self):
        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': ''
        })
        State.tenant_cache[1]['https_allowed']['admin'] = False
        yield self.assertFailure(handler.post(), errors.TorNetworkRequired)

    @inlineCallbacks
    def test_invalid_login_wrong_password(self):
        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': 'INVALIDPASSWORD',
            'authcode': '',
        })

        yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

    @inlineCallbacks
    def test_failed_login_counter(self):
        failed_login = 5
        for _ in range(0, failed_login):
            handler = self.request({
                'tid': 1,
                'username': 'admin',
                'password': 'INVALIDPASSWORD',
                'authcode': '',
            })

            yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

        self.assertEqual(Settings.failed_login_attempts[1], failed_login)

    @inlineCallbacks
    def test_single_session_per_user(self):
        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': '',
        })

        r1 = yield handler.post()

        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': '',
        })

        r2 = yield handler.post()

        self.assertTrue(Sessions.get(r1['session_id']) is None)
        self.assertTrue(Sessions.get(r2['session_id']) is not None)

    @inlineCallbacks
    def test_session_is_revoked(self):
        auth_handler = self.request({
            'tid': 1,
            'username': 'receiver1',
            'password': helpers.VALID_PASSWORD1,
            'authcode': '',
        })

        r1 = yield auth_handler.post()

        user_handler = self.request({}, headers={'x-session': r1['session_id']},
                                        handler_cls=UserInstance)

        # The first_session is valid and the request should work
        yield user_handler.get()

        # The second authentication invalidates the first session
        auth_handler = self.request({
            'tid': 1,
            'username': 'receiver1',
            'password': helpers.VALID_PASSWORD1,
            'authcode': '',
        })

        r2 = yield auth_handler.post()

        user_handler = self.request({}, headers={'x-session': r1['session_id']},
                                        handler_cls=UserInstance)

        # The first_session should now deny access to authenticated resources
        yield self.assertRaises(errors.NotAuthenticated, user_handler.get)

        # The second_session should have no problems.
        user_handler = self.request({}, headers={'x-session': r2['session_id']},
                                        handler_cls=UserInstance)

        yield user_handler.get()

    @inlineCallbacks
    def test_login_reject_on_ip_filtering(self):
        State.tenant_cache[1]['ip_filter']['admin'] = '192.168.2.0/24'

        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': ''
        }, client_addr=IPv4Address('TCP', '192.168.1.1', 12345))
        yield self.assertFailure(handler.post(), errors.AccessLocationInvalid)

    @inlineCallbacks
    def test_login_success_on_ip_filtering(self):
        State.tenant_cache[1]['ip_filter']['admin'] = '192.168.2.0/24'

        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': ''
        }, client_addr=IPv4Address('TCP', '192.168.2.1', 12345))
        response = yield handler.post()
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)


class TestReceiptAuth(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.ReceiptAuthHandler

    @inlineCallbacks
    def test_invalid_whistleblower_login(self):
        handler = self.request({
            'receipt': 'INVALIDRECEIPT',
        })
        yield self.assertFailure(handler.post(), errors.InvalidAuthentication)

    @inlineCallbacks
    def test_successful_whistleblower_login(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.lastReceipt,
        })
        handler.request.client_using_tor = True
        response = yield handler.post()
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)

    @inlineCallbacks
    def test_accept_whistleblower_login_in_https(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.lastReceipt,
        }, headers={'X-Tor2Web': 'whatever'})
        State.tenant_cache[1]['https_allowed']['whistleblower'] = True
        response = yield handler.post()
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)

    @inlineCallbacks
    def test_deny_whistleblower_login_in_https(self):
        yield self.perform_full_submission_actions()
        handler = self.request({
            'receipt': self.lastReceipt
        }, headers={'X-Tor2Web': 'whatever'})
        State.tenant_cache[1]['https_allowed']['whistleblower'] = False
        yield self.assertFailure(handler.post(), errors.TorNetworkRequired)

    @inlineCallbacks
    def test_single_session_per_whistleblower(self):
        """
        Asserts that the first_id is dropped from Sessions and requests
        using that session id are rejected
        """
        yield self.perform_full_submission_actions()

        handler = self.request({
            'receipt': self.lastReceipt
        })

        handler.request.client_using_tor = True
        response = yield handler.post()
        first_id = response['session_id']

        wbtip_handler = self.request(headers={'x-session': first_id},
                                     handler_cls=WBTipInstance)
        yield wbtip_handler.get()

        handler = self.request({
            'receipt': self.lastReceipt
        })

        response = yield handler.post()
        second_id = response['session_id']

        wbtip_handler = self.request(headers={'x-session': first_id},
                                     handler_cls=WBTipInstance)
        yield self.assertRaises(errors.NotAuthenticated, wbtip_handler.get)

        self.assertTrue(Sessions.get(first_id) is None)

        valid_session = Sessions.get(second_id)
        self.assertTrue(valid_session is not None)

        self.assertEqual(valid_session.user_role, 'whistleblower')

        wbtip_handler = self.request(headers={'x-session': second_id},
                                     handler_cls=WBTipInstance)
        yield wbtip_handler.get()


class TestSessionHandler(helpers.TestHandlerWithPopulatedDB):
    @inlineCallbacks
    def test_successful_admin_logout(self):
        self._handler = authentication.AuthenticationHandler

        # Login
        handler = self.request({
            'tid': 1,
            'username': 'admin',
            'password': helpers.VALID_PASSWORD1,
            'authcode': ''
        })

        response = yield handler.post()
        self.assertTrue(handler.session is None)
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)

        self._handler = authentication.SessionHandler

        # Logout
        session_id = response['session_id']
        handler = self.request({}, headers={'x-session': session_id})
        yield handler.delete()
        self.assertEqual(len(Sessions), 0)

    @inlineCallbacks
    def test_successful_whistleblower_logout(self):
        self._handler = authentication.ReceiptAuthHandler

        yield self.perform_full_submission_actions()

        handler = self.request({
            'receipt': self.lastReceipt
        })

        handler.request.client_using_tor = True

        response = yield handler.post()
        self.assertTrue(handler.session is None)
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)

        self._handler = authentication.SessionHandler

        # Logout
        handler = self.request({}, headers={'x-session': response['session_id']})
        yield handler.delete()
        self.assertEqual(len(Sessions), 0)


class TestTokenAuth(helpers.TestHandlerWithPopulatedDB):
    _handler = authentication.TokenAuthHandler

    # since all logins for roles admin, receiver and custodian happen
    # in the same way, the following tests are performed on the admin user.

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        session = Sessions.new(1, self.dummyReceiver_1['id'], 1, 'receiver', False, False, '', '')
        self.authtoken = session.id

    @inlineCallbacks
    def test_successful_login(self):
        handler = self.request({
            'authtoken': self.authtoken,
        })

        response = yield handler.post()
        self.assertTrue('session_id' in response)
        self.assertEqual(len(Sessions), 1)
