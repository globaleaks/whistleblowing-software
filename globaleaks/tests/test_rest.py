from cyclone.util import ObjectDict as OD
from twisted.trial import unittest

from globaleaks.rest import handlers, api

class DummyReqWrapper(handlers.GLBackendHandler):
    def __init__(self):
        pass


class RestTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_submission(self):
        class DummySubWrapper(handlers.submissionHandler):
            def __init__(self):
                pass

        sub = DummySubWrapper()
        sub.target.handler = OD()

        ret1 = sub.handle('files', 'foo', arg='bar')
        ret2 = sub.handle('status', '123456789')
        ret3 = sub.handle('finalize', '123456789')
        # XXX have better tests
        self.assertEqual(type(dict()), type(ret1))
        self.assertEqual(type(dict()), type(ret2))
        self.assertEqual(type(dict()), type(ret3))

