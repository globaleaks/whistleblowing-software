# -*- coding: utf-8 -*-

import re

from globaleaks.utils import agent

class TorExitList(set):
    def processData(self, data):
        self.clear()

        for ip in re.findall( r'ExitAddress ([^ ]*) ', data):
            self.add(ip)

    def update(self):
        pageFetchedDeferred = agent.getPageSecurely('https://check.torproject.org/exit-addresses')
        pageFetchedDeferred.addCallback(self.processData)
        return pageFetchedDeferred
