from globaleaks.handlers import css
from globaleaks.tests import helpers

# FIXME this tests does not really test the handler but
# simply asses the code coverage.

class TestLTRFileCSS(helpers.TestGL):
    _handler = css.LTRCSSFileHandler

    def test_get(self):
        handler = self.request({})
        yield handler.get()
        self.assertEqual(handler.get_status(), 200)


class TestRTLFileCSS(helpers.TestGL):
    _handler = css.RTLCSSFileHandler

    def test_get(self):
        handler = self.request({})
        yield handler.get()
        self.assertEqual(handler.get_status(), 200)

