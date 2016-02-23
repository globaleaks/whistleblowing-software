from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import css
from globaleaks.tests import helpers


# FIXME this tests does not really test the handler but
# simply asses the code coverage.

class TestFileCSS(helpers.TestHandler):
    _handler = css.CSSFileHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request({})
        yield handler.get()
        self.assertEqual(handler.get_status(), 200)
