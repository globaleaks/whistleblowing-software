# -*- coding: UTF-8
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)

import sys

from globaleaks.settings import GLSetting
from globaleaks.utils.utility import log, is_expired
from globaleaks.jobs.base import GLJob


__all__ = ['APSSessionManagement']

class APSSessionManagement(GLJob):

    def operation(self):
        """
        This scheduler is responsible of:
            - Removal of expired sessions
            - Reset of failed login attempts counters
        """

        # Removal of expired sessions
        try:
            # this list is needed because we can't do "del"
            # on a list during a loop on it without breaking the loop.
            sid_to_remove = []

            for session_id in GLSetting.sessions:
                checkd_session = GLSetting.sessions[session_id]

                if is_expired(checkd_session.refreshdate,
                              seconds=GLSetting.defaults.lifetimes[checkd_session.role]):
                    sid_to_remove.append(session_id)

            for expired_sid in sid_to_remove:
                del GLSetting.sessions[expired_sid]

            if len(sid_to_remove):
                log.debug("Expired %d sessions" % len(sid_to_remove))

        except Exception as excep:
            log.err("Exception failure in session cleaning routine (%s)" % excep.message)
            sys.excepthook(*sys.exc_info())

        # Reset of failed login attempts counters
        GLSetting.failed_login_attempts = 0
