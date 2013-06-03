from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers
from globaleaks.handlers import authentication, admin
from globaleaks.rest import errors
from globaleaks.settings import GLSetting

class TestAuthentication(helpers.TestHandler):
    _handler = authentication.AuthenticationHandler

    @inlineCallbacks
    def test_successful_admin_login(self):
        handler = self.request({
           'username': 'admin',
           'password': 'globaleaks',
           'role': 'admin'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

    @inlineCallbacks
    def test_accept_admin_login_in_tor2web(self):
        handler = self.request({
            'username': 'admin',
            'password': 'globaleaks',
            'role': 'admin'
        }, headers={'X-Tor2Web': 'whatever'})
        GLSetting.memory_copy.tor2web_admin = True
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

    @inlineCallbacks
    def test_successful_receiver_login(self):
        handler = self.request({
           'username': self.dummyReceiver['username'],
           'password': helpers.DEFAULT_PASSWORD,
           'role': 'receiver'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

    @inlineCallbacks
    def test_successful_whistleblower_login(self):
        handler = self.request({
           'username': '',
           'password': self.dummyWBTip,
           'role': 'wb'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

    @inlineCallbacks
    def test_successful_admin_logout(self):
        handler = self.request({
            'username': 'admin',
            'password': 'globaleaks',
            'role': 'admin'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

        handler = self.request()
        success = yield handler.delete()
        self.assertTrue(handler.current_user is None)

    @inlineCallbacks
    def test_successful_receiver_logout(self):
        handler = self.request({
            'username': self.dummyReceiver['username'],
            'password': helpers.DEFAULT_PASSWORD,
            'role': 'receiver'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

        handler = self.request()
        success = yield handler.delete()
        self.assertTrue(handler.current_user is None)

    @inlineCallbacks
    def test_successful_whistleblower_logout(self):
        handler = self.request({
            'username': '',
            'password': self.dummyWBTip,
            'role': 'wb'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

        handler = self.request()
        success = yield handler.delete()
        self.assertTrue(handler.current_user is None)

    def test_invalid_admin_login_wrong_password(self):
        handler = self.request({
           'username': 'admin',
           'password': 'INVALIDPASSWORD',
           'role': 'admin'
        })
        d = handler.post()
        self.assertFailure(d, errors.InvalidAuthRequest)
        return d

    def test_invalid_receiver_login_wrong_password(self):
        handler = self.request({
           'username': 'receiver',
           'password': 'INVALIDPASSWORD',
           'role': 'receiver'
        })
        d = handler.post()
        self.assertFailure(d, errors.InvalidAuthRequest)
        return d

    def test_invalid_whistleblower_login_wrong_receipt(self):
        handler = self.request({
           'username': '',
           'password': 'INVALIDPASSWORD',
           'role': 'wb'
        })
        d = handler.post()
        self.assertFailure(d, errors.InvalidAuthRequest)
        return d

    def test_invalid_input_format_missing_role(self):
        handler = self.request({
           'username': '',
           'password': '',
        })
        d = handler.post()
        self.assertFailure(d, errors.InvalidInputFormat)
        return d

    def test_invalid_input_format_wrong_role(self):
        handler = self.request({
           'username': 'ratzinger',
           'password': '',
           'role': 'pope'
        })
        d = handler.post()
        self.assertFailure(d, errors.InvalidInputFormat)
        return d

    @inlineCallbacks
    def test_failed_login_counter(self):
        handler = self.request({
            'username': self.dummyReceiver['username'],
            'password': 'INVALIDPASSWORD',
            'role': 'receiver'
        })

        failed_login = 8
        for i in xrange(0, failed_login):
            try:
                failure = yield handler.post()
                print type(failure)
            except errors.InvalidAuthRequest:
                continue
            except Exception as excep:
                print excep, "Has been raised wrongly"
                self.assertTrue(False)

        receiver_status = yield admin.get_receiver(self.dummyReceiver['receiver_gus'])
        self.assertTrue(receiver_status.has_key('failed_login'))
        self.assertEqual(receiver_status['failed_login'], failed_login)


