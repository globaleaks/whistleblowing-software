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
import os

from twisted.internet.defer import inlineCallbacks
from twisted.python import log

from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalFile, InternalTip, ReceiverTip, ReceiverFile, Receiver
from globaleaks.settings import transact
from globaleaks.utils import get_file_checksum
from globaleaks.handlers.files import SUBMISSION_DIR

__all__ = ['APSDelivery']


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

    for file_id, file_path in filesdict.iteritems():

        log.msg("Approaching checksum of file %s with path %s" % (file_id, file_path))
        file_location = os.path.join(SUBMISSION_DIR, file_path)

        checksum = get_file_checksum(file_location)
        processdict.update({file_id : checksum})

    return processdict


@transact
def receiver_file_align(store, filesdict, processdict):
    """
    This function is called when the single InternalFile has been processed,
    they became aligned respect the Delivery specification of the node.
    """

    for internalfile_id in filesdict.iterkeys():

        ifile = store.find(InternalFile, InternalFile.id == unicode(internalfile_id)).one()
        ifile.sha2sum = unicode(processdict.get(internalfile_id))

        # for each receiver intended to access to this file:
        for receiver_id in ifile.internaltip.receivers:
            log.msg("ReceiverFile creation for receiver_id %s, file %s" % (receiver_id, ifile.name) )
            receiverfile = ReceiverFile()
            receiverfile.receiver_id = receiver_id
            receiverfile.downloads = 0
            receiverfile.internalfile_id = internalfile_id
            receiverfile.internaltip_id = ifile.internaltip.id

            # Is the same until end-to-end crypto is not supported
            receiverfile.file_path = ifile.file_path
            store.add(receiverfile)

        log.msg("Processed InternalFile %s and update with checksum %s" % (ifile.name, ifile.sha2sum))

        ifile.mark = InternalFile._marker[1] # Ready (TODO review the marker)


def create_receivertip(store, receiver_id, internaltip, tier):
    """
    Create ReceiverTip for the required tier of Receiver.
    """
    receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
    
    log.msg('Creating ReceiverTip for: %s' % repr(receiver))

    if receiver.receiver_level != tier:
        log.msg('Receiver not of the right tier %s' % receiver_id)
        return

    receivertip = ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.access_counter = 0
    receivertip.expressed_pertinence = 0
    receivertip.receiver_id = receiver_id
    receivertip.mark = ReceiverTip._marker[0]
    store.add(receivertip)

    internaltip.receivertips.add(receivertip)


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

        internaltip.mark = internaltip._marker[2]

    promoted = store.find(InternalTip,
                        ( InternalTip.mark == InternalTip._marker[2],
                          InternalTip.pertinence_counter >= InternalTip.escalation_threshold ) )

    for internaltip in promoted:
        for receiver_id in internaltip.receivers:
            create_receivertip(store, receiver_id, internaltip, 2)
            # TODO interalfile_is_correct

        internaltip.mark = internaltip._marker[3]


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


