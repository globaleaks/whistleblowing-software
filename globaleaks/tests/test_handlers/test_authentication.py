from twisted.internet.defer import inlineCallbacks
from globaleaks.tests import helpers

from globaleaks.handlers import authentication
from globaleaks.rest import errors


class TestAuthentication(helpers.TestHandler):
    _handler = authentication.AuthenticationHandler

    @inlineCallbacks
    def test_successful_admin_login(self):
        handler = self.request({
           'username': 'admin',
           'password': 'spam',
           'role': 'admin'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

    @inlineCallbacks
    def test_successful_receiver_login(self):
        handler = self.request({
           'username': self.dummyReceiver['username'],
           'password': self.dummyReceiver['password'],
           'role': 'receiver'
        })
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

    @inlineCallbacks
    def test_successful_whistleblower_login(self):
        req = {'username': '',
           'password': self.dummyWhistleblowerTip['receipt'],
           'role': 'wb'
        }
        handler = self.request(req)
        success = yield handler.post()
        self.assertTrue('session_id' in self.responses[0])

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
           'username': 'some_receiver_name',
           'password': 'YYYYYYYY',
           'role': 'admin'
        })
        d = handler.post()
        self.assertFailure(d, errors.InvalidAuthRequest)
        return d

    def test_invalid_whistleblower_login_wrong_receipt(self):
        handler = self.request({
           'username': '',
           'password': 'YYYYYYYY',
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

