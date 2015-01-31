from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import css
from globaleaks.tests import helpers

# FIXME this tests does not really test the handler but
# simply asses the code coverage.

class TestLTRFileCSS(helpers.TestHandler):
    _handler = css.LTRCSSFileHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request({})
        yield handler.get()
        self.assertEqual(handler.get_status(), 200)


class TestRTLFileCSS(helpers.TestHandler):
    _handler = css.RTLCSSFileHandler

    @inlineCallbacks
    def test_get(self):
        handler = self.request({})
        yield handler.get()
        self.assertEqual(handler.get_status(), 200)

