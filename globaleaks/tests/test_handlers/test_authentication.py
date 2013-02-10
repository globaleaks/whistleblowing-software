from globaleaks.tests.test_handlers import helpers

from globaleaks.handlers import authentication
from globaleaks.rest import errors


class TestAuthentication(helpers.TestHandler):
    _handler = authentication.AuthenticationHandler

    def test_invalid_wb_login(self):
        req = {
           'username': '',
           'password': '',
        }
        # missing role keyword
        handler = self.request(req)
        d = handler.post()
        self.assertFailure(d, errors.InvalidInputFormat)

        return d

    def test_invalid_admin_login(self):
        pass

    def test_invalid_receiver_login(self):
        pass

    def test_valid_wb_login(self):
        pass

    def test_valid_admin_login(self):
        pass

