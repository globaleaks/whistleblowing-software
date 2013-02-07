# -*- coding: UTF-8
#
#   delivery_sched
#   **************
#
# Implements the delivery operations performed when a new submission
# is created, or a new file is append to an existing Tip. delivery 
# works on the file and on the fields, not in the comments.
#
# Call also the FileProcess working point, in order to verify which
# kind of file has been submitted.

from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from globaleaks.transactors.asyncoperations import AsyncOperations
from twisted.internet.defer import inlineCallbacks
from datetime import datetime

__all__ = ['APSDelivery']

class APSDelivery(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is process/validate the files, compute checksum, and
        apply the delivery method configured.

        """
        print "fileproces now"

        try:
            (itip_info, new_files) = yield AsyncOperations().fileprocess()

            print "received tip", itip_info
            print "received file", new_files

            # answer contain the list of internaltip processed

            print "delivery now"
            results = yield AsyncOperations().delivery()

        except Exception, e:
            # TODO fatal log
            print "Unhandled exception in FileProcess and Delivery (%s)" % e

