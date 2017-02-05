# -*- encoding: utf-8 -*-

from globaleaks.tests import helpers
from globaleaks.utils.gettor import GetTor


class TestGetTor(helpers.TestGL):
    gettor = GetTor("/tmp")

    def test_getCurrentVersion(self):
        self.assertEqual("0", self.gettor.getCurrentVersion())

    def test_getLC(self):
        self.assertEqual('en-US', self.gettor.getLC("en-US,en;q=0.8,it;q=0.6"))
        self.assertEqual('en', self.gettor.getLC("en-XX,it;q=0.6"))
        self.assertEqual('it', self.gettor.getLC("xx-XX,xx;q=0.8,it;q=0.6"))

    def test_getOS(self):
        self.assertEqual('android', self.gettor.getOS('Mozilla/5.0 (Linux; Android 5.1.1; Nexus 5 Build/LMY48B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/43.0.2357.65 Mobile Safari/537.36'))
        self.assertEqual('iphone', self.gettor.getOS('Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'))
        self.assertEqual('ipad', self.gettor.getOS('Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'))
        self.assertEqual('osx', self.gettor.getOS('Mozilla/5.0 (Macintosh; Intel Mac OS X 9_1_3) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0.2 Safari/602.3.12'))
        self.assertEqual('other', self.gettor.getOS('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/55.0.2883.87 Chrome/55.0.2883.87 Safari/537.36'))
        self.assertEqual('other', self.gettor.getOS('mozilla/5.0 (windows phone 8.1; arm; trident/7.0; touch; rv:11.0; iemobile/11.0; nokia; lumia 520) like gecko'))

    def test_getTB(self):
        a = self.gettor.getTB('windows', 'en')
        self.assertEqual(a[0], 'application/x-msdownload')
        self.assertEqual(a[1], 'torbrowser-install-0_en.exe')

        b = self.gettor.getTB('osx', 'en')
        self.assertEqual(b[0], 'application/x-apple-diskimage')
        self.assertEqual(b[1], 'TorBrowser-0-osx32_en.dmg')

        c = self.gettor.getTB('other', 'en')
        self.assertEqual(c[0], None)
        self.assertEqual(c[1], None)
