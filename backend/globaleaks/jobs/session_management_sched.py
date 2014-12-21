# -*- coding: UTF-8
#   session_management_sched
#   **************
#

from globaleaks.settings import GLSetting
from globaleaks.jobs.base import GLJob
from globaleaks.utils.utility import log

__all__ = ['SessionManagementSchedule']

class SessionManagementSchedule(GLJob):

    def operation(self):
        """
        This scheduler is responsible of:
            - Reset of failed login attempts counters
        """

        if GLSetting.failed_login_attempts:
            log.debug("Reset to 0 the counter of failed login attemps (now %d)"
                      % GLSetting.failed_login_attempts)

        GLSetting.failed_login_attempts = 0
