
# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

import time
import datetime

from twisted.internet.defer import Deferred
from twisted.internet import reactor

from globaleaks.jobs.base import Job

class Delivery(Job):
    target = None
    def schedule(self, date):
        if isinstance(date, datetime.datetime):
            self.scheduledTime = time.mktime(date.timetuple())
        else:
            raise Exception("date argument must be an instance of datetime")

    def _run(self, *arg, **kw):
        d = self.run(*arg)
        return d

    def run(self, *arg):
        d = Deferred()
        f = open('/tmp/testingout.txt', "a+")
        f.write(str(arg)+'\n')
        f.close()
        return d

