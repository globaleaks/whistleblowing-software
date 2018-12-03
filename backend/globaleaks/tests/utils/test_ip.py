# -*- coding: utf-8 -*
import ipaddress

from twisted.trial import unittest

from globaleaks.utils import ip

class TestIPUtils(unittest.TestCase):
    def test_parse_csv_ip_ranges_to_ip_networks(self):
        ip_str = "192.168.1.1,10.0.0.0/8,::1,2001:db8::/32"
        ip_list = ip.parse_csv_ip_ranges_to_ip_networks(ip_str)

        self.assertEqual(len(ip_list), 4)

        self.assertIn(ipaddress.ip_network(u"192.168.1.1/32"), ip_list)
        self.assertIn(ipaddress.ip_network(u"10.0.0.0/8"), ip_list)
        self.assertIn(ipaddress.ip_network(u"::1/128"), ip_list)
        self.assertIn(ipaddress.ip_network(u"2001:db8::/32"), ip_list)

        # Now confirm we properly fail when garbage is appended
        ip_str = ip_str + ",abcdef"
        self.assertEqual(ip.parse_csv_ip_ranges_to_ip_networks(ip_str), [])
