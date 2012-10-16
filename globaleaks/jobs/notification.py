
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

class Notification(Job):
    def success(self):
        address = self.address
        receipt_id = self.receipt_id
        log.debug("Successfully run notification of %s to %s" % (receipt_id, address))
        # XXX add here logic to check if we have finished with all the
        # deliveries and delete the submisssion directory.

    def run(self, *arg):
        address = self.address
        receipt_id = self.receipt_id
        dummy_file = os.path.join(config.advanced.data_dir,
                'dummy_notifications.txt')

        with open(dummy_file, "a+") as f:
            f.write("Notification %s :"\
                    "http://127.0.0.1:8082/index.html#"\
                    "/status/%s" % (address, receipt_id))
            f.write("\n\n")
        log.debug("Doing dummy notification %s into %s" % (address, receipt_id))

