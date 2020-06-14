# -*- coding: utf-8 -*-
import re
from datetime import datetime
from twisted.trial import unittest

from globaleaks.utils import utility


class TestUtility(unittest.TestCase):
    def test_msdos_encode(self):
        strs = [
            ('This is \n news', 'This is \r\n news'),
            ('No\r\nreplace', 'No\r\nreplace'),
            ('No\r\n\nreplace', 'No\r\n\r\nreplace'),
            ('No', 'No'),
            ('\nNo\n\n', '\r\nNo\r\n\r\n'),
            ('\r\nNo\n\n', '\r\nNo\r\n\r\n'),
        ]

        for (i, o) in strs:
            self.assertEqual(utility.msdos_encode(i), o)

    def test_uuid4(self):
        self.assertIsNotNone(re.match(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
                                      utility.uuid4()))

    def test_datetime_null(self):
        self.assertEqual(utility.datetime_null(), datetime.utcfromtimestamp(0))

    def test_get_expiration(self):
        date = utility.get_expiration(15)
        self.assertEqual(date.hour, 00)
        self.assertEqual(date.minute, 00)
        self.assertEqual(date.second, 00)

    def test_is_expired(self):
        self.assertTrue(utility.is_expired(utility.datetime_null()))
        self.assertTrue(utility.is_expired(utility.datetime_now()))
        self.assertFalse(utility.is_expired(utility.datetime_never()))

    def test_datetime_to_pretty_str(self):
        self.assertEqual(utility.datetime_to_pretty_str(utility.datetime_null()),
                         'Thursday 01 January 1970 00:00 (UTC)')

    def test_bytes_to_pretty_str(self):
        self.assertEqual(utility.bytes_to_pretty_str("60000000001"), "60GB")
        self.assertEqual(utility.bytes_to_pretty_str("5000000001"), "5GB")
        self.assertEqual(utility.bytes_to_pretty_str("40000001"), "40MB")
        self.assertEqual(utility.bytes_to_pretty_str("3000001"), "3MB")
        self.assertEqual(utility.bytes_to_pretty_str("20001"), "20KB")
        self.assertEqual(utility.bytes_to_pretty_str("1001"), "1KB")
