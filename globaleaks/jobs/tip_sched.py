from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.externaltip import ReceiverTip

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
        log.debug("[D]", self.__class__, 'operation', datetime.today().ctime())

        internaltip_iface = InternalTip()
        receivertip_iface = ReceiverTip()

        internal_id_list = yield internaltip_iface.get_newly_generated()

        for id in internal_id_list:

            yield receivertip_iface.create_receiver_tips(id, 1)
            yield internaltip_iface.flip_mark(id, u'first')

        # loops over the InternalTip and checks the escalation threshold
        # It may require the creation of second-step Tips
        internal_id_list = yield internaltip_iface.get_newly_escalated()

        for id in internal_id_list:

            yield receivertip_iface.create_receiver_tips(id, 2)
            yield internaltip_iface.flip_mark(id, u'second')
