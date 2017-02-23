# -*- coding: utf-8 -*-

import re

from globaleaks.utils import agent
from globaleaks.utils.utility import log

class TorExitSet(set):
    """Set that keep the list of tor exit nodes ip using check.torproject.org"""
    def processData(self, data):
        log.debug('Fetching exit nodes\'s ip list')

        self.clear()

        for ip in re.findall( r'ExitAddress ([^ ]*) ', data):
            self.add(ip)

        log.debug('Retrieved: %d exit nodes\' ip' % len(self))

    def update(self):
        def errback(fail):
             log.err('Exit relay fetch failed: %s' % fail.value)

        pageFetchedDeferred = agent.getPageSecurely('https://check.torproject.org/exit-addresses')
        pageFetchedDeferred.addCallback(self.processData)
        pageFetchedDeferred.addErrback(errback)

        return pageFetchedDeferred

def should_redirect_tor(tor_addr, exit_relay_set, request):
    forwarded_ip = request.headers.get('X-Forwarded-For', None)
    if forwarded_ip is None:
        forwarded_ip = request.remote_ip

    if tor_addr is not None and forwarded_ip in exit_relay_set:
        return True
    return False
