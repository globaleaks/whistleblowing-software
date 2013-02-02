# -*- coding: UTF-8
#
#   tip_sched
#   *********
#
# Tip creation is an asyncronous operation, here implemented

from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from twisted.internet.defer import inlineCallbacks
from globaleaks.transactors.asyncoperations import AsyncOperations
from globaleaks.rest.errors import InvalidInputFormat

__all__ = ['APSTip']

class APSTip(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to check all the InternalTip
        and create the Tips for the receiver needing.

        Create the ReceiverTip only, because WhistleBlowerTip is
        created when submission is finalized, along with the receipt
        exchange.

        Only the Receiver marked as first tier receiver has a Tip now,
        the receiver marked as tier 2 (if configured in the context)
        had their Tip only when the escalation_threshold has reached 
        the requested value.
        """

        try:
            results = yield AsyncOperations().tip_creation()

        except InvalidInputFormat, e:

            # Log Internal Error
            print "Internal error: ", e

        # log results
