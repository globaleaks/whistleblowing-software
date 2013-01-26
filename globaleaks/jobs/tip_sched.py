# -*- coding: UTF-8
#
#   tip_sched
#   *********
#
# Tip creation is an asyncronous operation, here implemented

from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.externaltip import ReceiverTip, Comment
from globaleaks.models.receiver import Receiver
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

        internaltip_iface = InternalTip()
        receivertip_iface = ReceiverTip()
        receiver_iface = Receiver()

        internal_tip_list = yield internaltip_iface.get_itips_by_maker(u'new', False)

        # TODO for each itip
            # TODO get file status


        if len(internal_tip_list):
            log.debug("TipSched: found %d new Tip" % len(internal_tip_list) )

        for internaltip_desc in internal_tip_list:

            for receiver_gus in internaltip_desc['receivers']:

                receiver_desc = yield receiver_iface.get_single(receiver_gus)

                # check if the Receiver Tier is the first
                if int(receiver_desc['receiver_level']) != 1:
                    continue

                receivertip_desc = yield receivertip_iface.new(internaltip_desc, receiver_desc)
                print "Created rTip", receivertip_desc['tip_gus'], "for", receiver_desc['name']

            try:
                # switch the InternalTip.mark for the tier supplied
                yield internaltip_iface.flip_mark(internaltip_desc['internaltip_id'], internaltip_iface._marker[1])
            except:
                # ErrorTheWorldWillEndSoon("Goodbye and thanks for all the fish")
                print "Internal error"
                raise


        # Escalation is not working at the moment, may be well engineered the function
        # before, permitting various layer of receivers.
        #
        # loops over the InternalTip and checks the escalation threshold
        # It may require the creation of second-step Tips
        escalated_itip_list = yield internaltip_iface.get_itips_by_maker(internaltip_iface._marker[1], True)

        if len(escalated_itip_list):
            log.debug("TipSched: %d Tip are escalated" % len(escalated_itip_list) )

        # This event has to be notified as system Comment
        comment_iface = Comment()

        for itip in escalated_itip_list:
            itip_id = int(itip['internaltip_id'])

            yield comment_iface.add_comment(itip_id, u"Escalation threshold has been reached", u'system')
            # XXX missing part new
            yield internaltip_iface.flip_mark(itip_id, internaltip_iface._marker[2])
            log.debug("TipSched: escalated %d ReceiverTip for the iTip %d" % (receivertip_created, itip_id))
