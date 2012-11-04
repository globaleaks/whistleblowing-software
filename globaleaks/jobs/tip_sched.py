from globaleaks.utils import log
from globaleaks.jobs.base import GLJob
from datetime import datetime
from twisted.internet.defer import inlineCallbacks

from globaleaks.models.submission import Submission
from globaleaks.models.context import Context

from globaleaks.models.tip import InternalTip, ReceiverTip

__all__ = ['APSTip']

class APSTip(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to check all the submission
        marked as 'finalized', and convert them in Tips for 
        every receiver.
        Create the ReceiverTip only, because WhistleBlowerTip is 
        created when submission is finalized, along with the receipt
        exchange.

        Only the Receiver marked as first tier receiver has a Tip now,
        the receiver marked as tier 2 (if configured in the context)
        had their Tip only when the escalation_threshold has reached 
        the requested value.
        """
        log.debug("[D]", self.__class__, 'operation', datetime.today().ctime())

        submission_iface = Submission()

        finalized_submissions = yield submission_iface.get_submissions(mark=u'finalized')

        for single_submission in finalized_submissions:
            print "I've to create ReceiverTip about:", single_submission

            context_iface = Context()

            yield context_iface.create_receiver_tips(single_submission)
            # create ReceiverTip, status = u'not notified'

        # loops over the InternalTip and checks the escalation threshold
        # It may require the creation of second-step Tips

        not_finalized = yield submission_iface.get_submissions(mark=u'incomplete')

        for single_submission in not_finalized:
            print "not finalized", single_submission


    def _create_receiver_tips(self, submissionDescriptionDict):
        pass

        # store = self.getStore('tip_sched - create_receiver_tips')

        # the Storm information about Context/Receiver are been already included
        # in submissionDescriptionDict, need to be open:
        #
        # InternalTip - to update tracking of ReceiverTip [gus and notification status]
        # Submission - for remove the temporary submission
        # Folder - to be determined the operation sequence, along with the delivery logic


        """
        receiver_tips = context.create_receiver_tips(internal_tip)

        log.debug("Looking up receivers")
        for receiver in context.receivers:
            log.debug("[D] %s %s " % (__file__, __name__), "Submission", "create_tips", "Creating tip for %s" % receiver.receiver_gus)
            receiver_tip = ReceiverTip()
            receiver_tip.internaltip = internal_tip
            receiver_tip.new(receiver.receiver_gus)
            store.add(receiver_tip)
            log.debug("Tip created")


            At the moment the scheduler queue is bugged,


            log.debug("Creating delivery jobs")
            delivery_job = Delivery()
            delivery_job.submission_gus = submission_gus
            delivery_job.receipt_id = receiver_tip.address
            work_manager.add(delivery_job)

            log.debug("Added delivery to %s to the work manager" % receiver.receiver_gus)

            notification_job = Notification()
            notification_job.address = receiver.name
            notification_job.receipt_gus = receiver_tip.address
            work_manager.add(notification_job)

            log.debug("Deleting the temporary submission %s" % submission.submission_gus)

            store.remove(submission)
            # maybe also this operation can give the lock problem

            try:
                store.commit()
            except Exception, e:
                log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", type(submission_gus), "file_name", type(file_name), "Could not create submission" )
                log.err(e)
                store.rollback()
                store.close()

            log.debug("create_tips complete, commit done, closing storage")
            store.close()

            """

