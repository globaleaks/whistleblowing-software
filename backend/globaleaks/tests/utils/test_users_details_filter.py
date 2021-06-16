# -*- coding: utf-8 -*-
import json
from globaleaks.utils.users_details_filter import UserDetailsFilter
from collections import OrderedDict
from twisted.trial import unittest
from globaleaks.utils.crypto import generateRandomKey

class TestLogUtilities(unittest.TestCase):
    def test_user_details_filter_removes_bgp_formatted_string(self):
        mail_body = '''some text before pgp string
        -----BEGIN PGP PUBLIC KEY BLOCK-----
        Comment: Alice's revocation certificate
        Comment: https://www.ietf.org/id/draft-bre-openpgp-samples-01.html
        iHgEIBYIACAWIQTrhbtfozp14V6UTmPyMVUMT0fjjgUCXaWkOwIdAAAKCRDyMVUM
        T0fjjoBlAQDA9ukZFKRFGCooVcVoDVmxTaHLUXlIg9TPh2f7zzI9KgD/SLNXUOaH
        O6TozOS7C9lwIHwwdHdAxgf5BzuhLT9iuAM==Tm8h
        -----END PGP PUBLIC KEY BLOCK-----
        some text after pgp string'''

        user_details_filter = UserDetailsFilter(mail_body)
        expected_formatted_string = '''some text before pgp string
        * filtered pgp string *
        some text after pgp string'''
        self.assertEqual(user_details_filter.filtered_string(), expected_formatted_string)

    def test_user_details_filter_removes_session_id_details(self):
        session = {"session_id" : generateRandomKey()}
        mail_body = json.dumps(session)
        user_details_filter = UserDetailsFilter(mail_body)
        expected_formatted_string = '{"session_id":filtered,"}'
        self.assertEqual(user_details_filter.filtered_string(), expected_formatted_string)

        session = OrderedDict([("session_id", generateRandomKey()), ("user_id", 12345)])
        mail_body = json.dumps(session)
        user_details_filter = UserDetailsFilter(mail_body)
        expected_formatted_string = '{"session_id":filtered,", "user_id": 12345}'
        self.assertEqual(user_details_filter.filtered_string(), expected_formatted_string)

    def test_user_details_filter_removes_email_information(self):
        mail_body = "abcd@defg.com"
        user_details_filter = UserDetailsFilter(mail_body)
        self.assertEqual(user_details_filter.filtered_string(), 'filtered@email')
