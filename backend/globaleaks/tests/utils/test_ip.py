# -*- coding: utf-8 -*
from twisted.trial import unittest

from globaleaks.utils import ip


class TestIPUtils(unittest.TestCase):
    def test_parse_csv_ip_ranges_to_ip_networks(self):
        ip_str = "192.168.1.1,10.0.0.0/8,::1,2001:db8::/32"
        self.assertTrue(ip.check_ip("192.168.1.1", ip_str))

        ip_str = "192.168.1.2,10.0.0.0/8,::1,2001:db8::/32"
        self.assertFalse(ip.check_ip("192.168.1.1", ip_str))

        ip_str = "192.168.1.2,10.0.0.0/8,::1,2001:db8::/32"
        self.assertTrue(ip.check_ip("10.0.0.1", ip_str))

        ip_str = "192.168.1.2, 10.0.0.0/8, ::1,2001:db8::/32"
        self.assertTrue(ip.check_ip("2001:db8::2", ip_str))
