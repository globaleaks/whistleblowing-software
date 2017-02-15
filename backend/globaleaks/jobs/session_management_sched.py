# -*- coding: UTF-8
#   session_management_sched
#   **************
#

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log

__all__ = ['SessionManagementSchedule', 'ExitRelayRefreshSchedule']


class SessionManagementSchedule(GLJob):
    name = "Session Management"
    interval = 60
    monitor_interval = 10

    def operation(self):
        """
        This scheduler is responsible for:
            - Reset of failed login attempts counters
        """
        if GLSettings.failed_login_attempts:
            log.debug("Reset to 0 the counter of failed login attemps (now %d)"
                      % GLSettings.failed_login_attempts)

        GLSettings.failed_login_attempts = 0


class ExitRelayRefreshSchedule(GLJob):
    name = "ExitRelayRefresh"
    interval = 3600

    def operation(self):
        self._operation()

    @inlineCallbacks
    def _operation(self):
        """Issue an request to tor.checkstatus to update the exit relay list
        """
        log.debug('Fetching exit relays')
        yield GLSettings.state.tor_exit_set.update()
        log.debug('Retrieved: %d exit relays' % len(GLSettings.state.tor_exit_set))
