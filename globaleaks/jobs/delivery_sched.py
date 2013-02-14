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
from twisted.internet.defer import inlineCallbacks
from twisted.python import log

from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalFile, InternalTip, ReceiverTip, ReceiverFile, Receiver
from globaleaks.settings import transact
from globaleaks.utils import get_file_checksum

__all__ = ['APSDelivery']


def internalfile_is_correct(internalfile):
    """
    Every InternalFile need to have a ReceiverFile associated,
    and if required a dedicated treatemenet (eg, per-receiver
    encryption) need to be sets here.
    """
    pass

@transact
def file_preprocess(store):
    """
    This function roll over the InternalFile uploaded, extract a path:id
    association. pre process works in the DB only, do not perform filesystem OPs
    """
    files = store.find(InternalFile, InternalFile.mark == InternalFile._marker[0])

    filesdict = {}
    for file in files:
        filesdict.update({file.id : file.file_path})

    return filesdict

def file_process(filesdict):
    processdict = {}
    print filesdict
    for file_id, file_path in filesdict.iteritems():
        log.msg("Approaching checksum of file %s with path %s" % (file_id, file_path))
        checksum = get_file_checksum(file_path)
        processdict.update({file_id : checksum})


@transact
def receiver_file_align(store, filesdict, processdict):
    """
    This function is called when the single InternalFile has been processed,
    they became aligned respect the Delivery specification of the node.
    """



def create_receivertip(store, receiver_id, internaltip, tier):
    """
    Create ReceiverTip for the required tier of Receiver.
    """

    receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()

    log.msg('Creating ReceiverTip for: %s' % repr(receiver))

    if receiver.receiver_level != tier:
        return

    receivertip = ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.access_counter = 0
    receivertip.expressed_pertinence = 0
    receivertip.receiver_id = receiver_id
    receivertip.mark = ReceiverTip._marker[0]

    store.add(receivertip)

@transact
def tip_creation(store):
    """
    look for all the finalized InternalTip, create ReceiverTip for the
    first tier of Receiver, and shift the marker in 'first' aka di,ostron.zo
    """
    finalized = store.find(InternalTip, InternalTip.mark == InternalTip._marker[1])

    for internaltip in finalized:
        for receiver_id in internaltip.receivers:
            create_receivertip(store, receiver_id, internaltip, 1)
            # TODO interalfile_is_correct

        internaltip.mark = internaltip._marker[1]

    promoted = store.find(InternalTip,
                        ( InternalTip.mark == InternalTip._marker[2],
                          InternalTip.pertinence_counter >= InternalTip.escalation_threshold ) )

    for internaltip in promoted:
        for receiver_id in internaltip.receivers:
            create_receivertip(store, receiver_id, internaltip, 2)
            # TODO interalfile_is_correct

        internaltip.mark = internaltip._marker[2]


class APSDelivery(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is process/validate the files, compute checksum, and
        apply the delivery method configured.

        """

        # ==> Submission && Escalation
        yield tip_creation()


        # ==> Files && Files update

        filesdict = yield file_preprocess()
        # return a dict { "file_uuid" : "file_path" }

        try:
            # perform FS base processing, outside the transactions
            processdict = file_process(filesdict)
            # return a dict { "file_uuid" : checksum }
        except OSError, e:
            # TODO fatal log here!
            log.err("Fatal OS error in processing file: %s" % e)

        # TODO, delivery not implemented ATM
        yield receiver_file_align(filesdict, processdict)


