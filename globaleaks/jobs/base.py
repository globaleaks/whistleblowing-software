# -*- coding: UTF-8
#   jobs/base
#   *********
#
# Base class for implement the scheduled tasks

from apscheduler.scheduler import Scheduler
from datetime import date
from globaleaks import utils

class GLJob:

    def force_execution(self, aps=None, seconds=0):
        """
        @aps: Advanced Python Scheduler object
        seconds: number of seconds to await before operation start
        """
        if not seconds:
            self.operation()
        else:
            # this hours=1 need to be managed with CEST/CET timezone checks
            plan_exec = utils.utcFutureDate(hours=1, seconds=seconds)

            print "Stored execution of %s postpone to %s" % \
                  (self.__class__.__name__, utils.prettyDateTime(plan_exec) )

            aps.add_date_job(self.operation, plan_exec)
