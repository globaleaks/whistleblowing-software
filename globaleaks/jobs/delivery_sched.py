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

from globaleaks.jobs.base import GLJob
from globaleaks.transactors.asyncoperations import AsyncOperations
from globaleaks.models import InternalFile, InternalTip, ReceiverTip, ReceiverFile
from globaleaks.settings import transact
from twisted.internet.defer import inlineCallbacks

__all__ = ['APSDelivery']



class APSDelivery(GLJob):

    def flip_mark(self, target, source_m, dest_m):
        pass

    def internalfile_is_correct(self, internalfile):
        """
        Every InternalFile need to have a ReceiverFile associated,
        and if required a dedicated treatemenet (eg, per-receiver
        encryption) need to be sets here.
        """
        pass


    @transact
    def fileprocess(self, store):
        """
        This function roll over the InternalFile uploaded,
        complete the needed ReceiverTip
        """
        files = store.find(InternalFile, InternalFile.mark == InternalFile._marker[0])

        # files need to be processed
        # TODO

    def create_receivertip(self, store, receiver, internaltip):

        print "Creating ReceiverTip for", receiver.id, "for itip", internaltip.id
        initialization = {
            'internaltip_id' : internaltip.id,
            'access_counter' : 0,
            'expressed_pertinence' : 0,
            'receiver_id' : receiver.id,
            'notification_mark' : ReceiverTip._marker[0],
        }

        receivertip = ReceiverTip(initialization)
        store.add(receivertip)

    @transact
    def tip_creation(self, store):
        """
        look for all the finalized InternalTip, create ReceiverTip for the
        first tier of Receiver, and shift the marker in 'first' aka di,ostron.zo
        """
        finalized = store.find(InternalTip, InternalTip.mark == InternalTip._marker[1])

        for internaltip in finalized:
            for receiver in internaltip.receivers:
                if receiver.receiver_level == 1:
                    self.create_receivertip(store, receiver, internaltip)
                    # TODO interalfile_is_correct

            self.flip_mark(internaltip, InternalTip.mark[0], InternalTip.mark[1])

        promoted = store.find(InternalTip,
                            ( InternalTip.mark == InternalTip._marker[2],
                              InternalTip.pertinence_counter >= InternalTip.escalation_threshold ) )

        for internaltip in promoted:
            for receiver in internaltip.receivers:
                if receiver.receiver_level == 2:
                    self.create_receivertip(store, receiver, internaltip)
                    # TODO interalfile_is_correct

            self.flip_mark(internaltip, InternalTip.mark[1], InternalTip.mark[2])


    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is process/validate the files, compute checksum, and
        apply the delivery method configured.

        """
        # ==> Tip and Submission files upload
        # ==> only Submission hanlded now4

        yield self.fileprocess()

        # ==> Submission && Escalation
        yield self.tip_creation()

        # TODO, delivery not implemented ATM
        # ==> Files && Files update
        # yield delivery()


