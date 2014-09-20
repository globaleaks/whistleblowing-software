# -*- coding: UTF-8
#   session_management_sched
#   **************
#

import sys

from globaleaks.settings import GLSetting
from globaleaks.jobs.base import GLJob

__all__ = ['SessionManagementSchedule']

class SessionManagementSchedule(GLJob):

    def operation(self):
        """
        This scheduler is responsible of:
            - Reset of failed login attempts counters
        """

        # Reset of failed login attempts counters
        GLSetting.failed_login_attempts = 0
