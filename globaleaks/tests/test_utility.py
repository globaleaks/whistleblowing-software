from twisted.trial import unittest

from globaleaks.utils import utility

class TestUtility(unittest.TestCase):

    def test_log_encode_html_str(self):
        self.assertEqual(utility.log_encode_html("<"), '&lt;')
        self.assertEqual(utility.log_encode_html(">"), '&gt;')
        self.assertEqual(utility.log_encode_html("'"), '&#39;')
        self.assertEqual(utility.log_encode_html("/"), '&#47;')
        self.assertEqual(utility.log_encode_html("\\"), '&#92;')

        self.assertEqual(utility.log_encode_html("<>'/\\"), '&lt;&gt;&#39;&#47;&#92;')

    def test_log_remove_escapes(self):
        for c in map(chr, range(32)):
            self.assertNotEqual(utility.log_remove_escapes(c), c)

        for c in map(chr, range(127, 140)):
            self.assertNotEqual(utility.log_remove_escapes(c), c)

        start = ''.join(map(chr, range(32))) + ''.join(map(chr, range(127, 140)))

        end = ''
        for c in map(chr, range(32)):
            end += utility.log_remove_escapes(c)

        for c in map(chr, range(127, 140)):
            end += utility.log_remove_escapes(c)

        self.assertEqual(utility.log_remove_escapes(start), end) 
