from globaleaks.tests.test_handlers import helpers

from globaleaks.handlers import authentication
from globaleaks.rest import errors


class TestAuthentication(helpers.TestHandler):
    _handler = authentication.AuthenticationHandler

    def test_invalid_wb_login(self):
        # missing role keyword
        handler = self.request({
           'username': '',
           'password': '',
        })
        malformed = handler.post()
        self.assertFailure(malformed, errors.InvalidInputFormat)

        return malformed

    def test_invalid_admin_login(self):
        # missing role keyword
        handler = self.request({
           'username': '',
           'password': '',
        })
        malformed = handler.post()
        self.assertFailure(malformed, errors.InvalidInputFormat)

        malformed
    def test_invalid_receiver_login(self):
        # wrong username/password
        handler = self.request({
           'username': 'foobar',
           'password': 'spamcheese',
           'role': 'receiver'
        })
        failed = handler.post()
        self.assertFailure(failed, errors.InvalidAuthRequest)

        return failed


    def test_valid_wb_login(self):
        pass

    def test_valid_admin_login(self):
        pass

