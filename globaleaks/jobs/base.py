# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks

from datetime import datetime

from globaleaks import utils
from globaleaks.utils import log

class GLJob:

    def force_execution(self, aps=None, seconds=1):
        """
        @aps: Advanced Python Scheduler object
        seconds: number of seconds to await before operation start

        force execution do not execute immidiatly self.operation(),
        because we want be sure that is a thread start by APScheduler
        """
        plan_exec = utils.utc_future_date(hours=0, seconds=seconds)
        plan_exec += (datetime.now() - datetime.utcnow())

        try:
            aps.add_date_job(self.operation, plan_exec)
        except ValueError as exc:
            log.err("Failing in force schedule execution of %s planned at %s" %
                      (self.__class__.__name__, utils.pretty_date_time(plan_exec)))

        log.debug("Forced execution of %s at %s" %
                  (self.__class__.__name__, utils.pretty_date_time(plan_exec)))
