# -*- coding: utf-8
# Implement reset of variables related to sessions
from globaleaks.jobs.base import LoopingJob
from globaleaks.settings import Settings

__all__ = ['SessionManagementSchedule']


class SessionManagementSchedule(LoopingJob):
    name = "Session Management"
    interval = 60
    monitor_interval = 10

    def operation(self):
        """
        This scheduler is responsible for:
            - Reset of failed login attempts counters
            - Refresh of the api_token's suspension
        """
        Settings.failed_login_attempts = 0
        self.state.api_token_session_suspended = False
