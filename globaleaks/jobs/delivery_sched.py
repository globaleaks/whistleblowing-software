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
from globaleaks.models import InternalFile, InternalTip, ReceiverTip, ReceiverFile, Receiver
from globaleaks.settings import transact
from twisted.internet.defer import inlineCallbacks

__all__ = ['APSDelivery']


class APSDelivery(GLJob):

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

    def create_receivertip(self, store, receiver_id, internaltip, tier):

        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()

        print "Creating ReceiverTip for:", receiver.name, "id", receiver.id, "tier", receiver.receiver_level,\
            "for itip", internaltip.id, "Round for tier", tier, "RECEIVER TIP:", receiver.id, "username",\
            receiver.username, "password", receiver.password, "POPE YOU RESIGN HAAHAHAHH!!!!"

        if receiver.receiver_level != tier:
            return

        initialization = {
            'internaltip_id' : internaltip.id,
            'access_counter' : 0,
            'expressed_pertinence' : 0,
            'receiver_id' : receiver_id,
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
            for receiver_id in internaltip.receivers:
                self.create_receivertip(store, receiver_id, internaltip, 1)
                # TODO interalfile_is_correct

            # internaltip.mark = internaltip._marker[1]

        promoted = store.find(InternalTip,
                            ( InternalTip.mark == InternalTip._marker[2],
                              InternalTip.pertinence_counter >= InternalTip.escalation_threshold ) )

        for internaltip in promoted:
            for receiver_id in internaltip.receivers:
                self.create_receivertip(store, receiver_id, internaltip, 2)
                # TODO interalfile_is_correct

            # internaltip.mark = internaltip._marker[2]


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


