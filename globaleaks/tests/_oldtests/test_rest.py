
import sys

# hack to add globaleaks to the sys path
sys.path.insert(0, '../../')

from cyclone.util import ObjectDict as OD
from twisted.trial import unittest

class RestTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def disabled_test_submission(self):
        sub = submission.SubmissionRoot()
        sub.target.handler = OD()
        sub.method = 'POST'
        sub.arguments = ['foo']
        sub.keywordArguments = {'arg': 'bar'}
        ret1 = sub.handle('files')
        sub.arguments = ['123456789']
        ret2 = sub.handle('status')
        ret3 = sub.handle('finalize')
        # XXX have better tests
        self.assertEqual(type(dict()), type(ret1))
        self.assertEqual(type(dict()), type(ret2))
        self.assertEqual(type(dict()), type(ret3))


