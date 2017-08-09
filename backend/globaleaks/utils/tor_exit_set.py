# -*- coding: utf-8 -*-

import re

from globaleaks.utils.agent import get_page


EXIT_ADDR_URL = 'https://check.torproject.org/exit-addresses'

class TorExitSet(set):
    """Set that keep the list of Tor exit nodes ip using check.torproject.org"""
    def processData(self, data):
        self.clear()

        for ip in re.findall( r'ExitAddress ([^ ]*) ', data):
            self.add(ip)

    def update(self, agent):
        pageFetchedDeferred = get_page(agent, EXIT_ADDR_URL)
        pageFetchedDeferred.addCallback(self.processData)
        return pageFetchedDeferred
