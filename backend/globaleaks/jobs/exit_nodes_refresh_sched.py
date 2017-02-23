# -*- coding: UTF-8
# Implement refresh of the list of exit nodes IPs.

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log

__all__ = ['ExitNodesRefreshSchedule']

class ExitNodesRefreshSchedule(GLJob):
    name = "Exit Nodes Refresh"
    interval = 3600

    def operation(self):
        self._operation()

    @inlineCallbacks
    def _operation(self):
        """Issue a request to check.torproject.org to update the exit relay list"""
        log.debug('Fetching exit relays')
        try:
            yield GLSettings.state.tor_exit_set.update()
        except Exception as e:
            log.err('Exit relay fetch failed: %s' % e)
        log.debug('Retrieved: %d exit relays' % len(GLSettings.state.tor_exit_set))

