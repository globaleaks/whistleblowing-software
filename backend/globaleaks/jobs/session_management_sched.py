# -*- coding: UTF-8
#   session_management_sched
#   **************
#

from globaleaks.settings import GLSettings
from globaleaks.jobs.base import GLJob
from globaleaks.utils.utility import log

__all__ = ['SessionManagementSchedule']

class SessionManagementSchedule(GLJob):
    name = "Session Management"

    def operation(self):
        """
        This scheduler is responsible for:
            - Reset of failed login attempts counters
        """
        if GLSettings.failed_login_attempts:
            log.debug("Reset to 0 the counter of failed login attemps (now %d)"
                      % GLSettings.failed_login_attempts)

        GLSettings.failed_login_attempts = 0
