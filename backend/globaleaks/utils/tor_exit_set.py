# -*- coding: utf-8 -*-

import re

from globaleaks.utils.agent import get_page
from globaleaks.utils.utility import log

EXIT_ADDR_URL = 'https://check.torproject.org/exit-addresses'

class TorExitSet(set):
    """Set that keep the list of tor exit nodes ip using check.torproject.org"""
    def processData(self, data):
        log.debug('Fetching exit nodes\'s ip list')

        self.clear()

        for ip in re.findall( r'ExitAddress ([^ ]*) ', data):
            self.add(ip)

        log.debug('Retrieved: %d exit nodes\' IPs' % len(self))

    def update(self, agent):
        def errback(fail):
             log.err('Exit relay fetch failed: %s' % fail.value)

        pageFetchedDeferred = get_page(agent, EXIT_ADDR_URL)
        pageFetchedDeferred.addCallback(self.processData)
        pageFetchedDeferred.addErrback(errback)

        return pageFetchedDeferred
