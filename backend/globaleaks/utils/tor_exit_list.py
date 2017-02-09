# -*- coding: utf-8 -*-

import re

from globaleaks.utils import agent

class TorExitList(set):
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

def should_redirect_tor(glsettings, request):
    if glsettings.tor_address is not None and \
       request.remote_ip in glsettings.state.exit_relay_list:
        return True
    return False
