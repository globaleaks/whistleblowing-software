# -*- coding: utf-8 -*-

import re

from globaleaks.utils import agent

class TorExitSet(set):
    def processData(self, data):
        self.clear()

        for ip in re.findall( r'ExitAddress ([^ ]*) ', data):
            self.add(ip)

    def requestFailed(self, fail):
        pass

    def update(self):
        pageFetchedDeferred = agent.getPageSecurely('https://check.torproject.org/exit-addresses')
        pageFetchedDeferred.addCallback(self.processData)
        pageFetchedDeferred.addErrback(self.requestFailed)
        return pageFetchedDeferred

def should_redirect_tor(tor_addr, exit_relay_set, request):
    forwarded_ip = request.headers.get('X-Forwarded-For', None)
    if forwarded_ip is None:
        forwarded_ip = request.remote_ip

    if tor_addr is not None and forwarded_ip in exit_relay_set:
        return True
    return False
