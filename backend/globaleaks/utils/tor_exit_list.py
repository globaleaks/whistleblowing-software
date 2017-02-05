# -*- coding: utf-8 -*-

import re
from twisted.web.client import getPage
from globaleaks.utils.tls import TLSClientContextFactory


class TorExitList(set):
    def processData(self, data):
        self.clear()

        for ip in re.findall( r'ExitAddress ([^ ]*) ', data):
            self.add(ip)

    def update(self):
        pageFetchedDeferred = getPage('https://check.torproject.org/exit-addresses', TLSClientContextFactory('check.torproject.org'))
        pageFetchedDeferred.addCallback(self.processData)
        return pageFetchedDeferred
