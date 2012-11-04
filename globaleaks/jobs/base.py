from apscheduler.scheduler import Scheduler
from datetime import date

class GLJob:

    def force_execution(self, aps=None, seconds=0):
        """
        @aps: Advanced Python Scheduler object
        seconds: number of seconds to await before operation start
        """

        if not seconds:
            self.operation()
        else:
            print "TODO: postpone operation of", seconds
            #  aps.add_interval_job(self.operation, seconds=seconds)
            # remind: is not the correct way, need
            # add_date_job
