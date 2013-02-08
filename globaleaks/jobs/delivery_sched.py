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
        try:
            # ==> Tip and Submission files upload
            # ==> only Submission hanlded now
            (itip_info, new_files) = yield AsyncOperations().fileprocess()

            # Tip creation, because in this moment, don't care about the delivery
            # process, a local version of ReceiverTip would exists

            # ==> Submission && Escalation
            results = yield AsyncOperations().tip_creation()

            # ==> Files && Files update
            results = yield AsyncOperations().delivery()

        except AttributeError, e:
            # TODO fatal log
            print "Unexpected exception in FileProcess, Tip Creation or Delivery (%s)" % e

