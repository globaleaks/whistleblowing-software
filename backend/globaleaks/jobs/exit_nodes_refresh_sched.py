# -*- coding: UTF-8
# Implement refresh of the list of exit nodes IPs.

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log
from globaleaks.utils.mailutils import extract_exception_traceback_and_send_email

__all__ = ['ExitNodesRefreshSchedule']

class ExitNodesRefreshSchedule(GLJob):
    name = "Exit Nodes Refresh"
    interval = 3600

    def operation(self):
        # NOTE operation is intended to a be synchronous func. Here it is async
        self._operation()

    @inlineCallbacks
    def _operation(self):
        """Issue a request to check.torproject.org to update the exit relay list"""
        log.debug('Fetching exit relays')
        try:
            yield GLSettings.state.tor_exit_set.update()
        except Exception as e:
            log.err('Exit relay fetch failed: %s' % e)
            # TODO move exception mail spool out of thread
            extract_exception_traceback_and_send_email(e)
        log.debug('Retrieved: %d exit relays' % len(GLSettings.state.tor_exit_set))
