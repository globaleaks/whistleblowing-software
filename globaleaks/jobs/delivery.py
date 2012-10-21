
# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

import time
import datetime
import shutil
import os

from twisted.internet.defer import Deferred
from twisted.internet import reactor

from globaleaks import config
from globaleaks.utils import log
from globaleaks.jobs.base import Job

class Delivery(Job):
    log.debug("[D] %s %s " % (__file__, __name__), "Class Delivery", "Job", Job)
    target = None
    def schedule(self, date):
        if isinstance(date, datetime.datetime):
            self.scheduledTime = time.mktime(date.timetuple())
        else:
            raise Exception("date argument must be an instance of datetime")

    def _run(self, *arg, **kw):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Delivery", "_run")
        d = self.run(*arg)
        return d

    def success(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Delivery", "success")
        submission_id = self.submission_id
        receipt_id = self.receipt_id
        log.debug("Successfully run %s delivery %s" % (submission_id, receipt_id))
        # XXX add here logic to check if we have finished with all the
        # deliveries and delete the submisssion directory.

    def run(self, *arg):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Delivery", "run")
        submission_id = self.submission_id
        receipt_id = self.receipt_id
        if not os.path.isdir(config.advanced.delivery_dir):
            log.debug("%s does not exist. creating it." % config.advanced.delivery_dir)
            os.mkdir(config.advanced.delivery_dir)

        dst_dir = os.path.join(config.advanced.delivery_dir, receipt_id)
        #if not os.path.isdir(receipt_dir):
        #    log.debug("%s does not exist. creating it." % receipt_dir)
        #    os.mkdir(receipt_dir)

        src_dir = os.path.join(config.advanced.submissions_dir, submission_id)

        log.debug("Copying %s into %s" % (src_dir, dst_dir))
        shutil.copytree(src_dir, dst_dir)

