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
import sys

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalFile, InternalTip, ReceiverTip, \
                              ReceiverFile, Receiver
from globaleaks.settings import transact, GLSetting
from globaleaks.utils import get_file_checksum, log, pretty_date_time
from globaleaks.security import GLBGPG
from globaleaks.handlers.admin import admin_serialize_receiver

__all__ = ['APSDelivery']

@transact
def file_preprocess(store):
    """
    This function roll over the InternalFile uploaded, extract a path:id
    association. pre process works in the DB only, do not perform filesystem OPs
    act only on files marked as 0 ('not processed') and associated to InternalTip
    'finalized'
    """
    files = store.find(InternalFile, InternalFile.mark == InternalFile._marker[0])

    filesdict = {}
    for filex in files:
        if not filex.internaltip:
            log.err("(file_preprocess) Integrity failure: the file %s of %s"\
                    "has not an InternalTip assigned (path: %s)" %
                    (filex.name, pretty_date_time(filex.creation_date), filex.file_path) )

            store.remove(filex)

            try:
                os.unlink( os.path.join(GLSetting.submission_path, filex.file_path) )
            except OSError as excep:
                log.err("Unable to remove %s in integrity fixing routine: %s" %
                    (filex.file_path, excep.strerror) )
            continue

        if filex.internaltip.mark == InternalTip._marker[0]:
            continue

        filesdict.update({filex.id : filex.file_path})

    return filesdict


# It's not a transact because works on FS
def file_process(filesdict):
    processdict = {}

    for file_id, file_path in filesdict.iteritems():

        file_location = os.path.join(GLSetting.submission_path, file_path)
        checksum = get_file_checksum(file_location)
        processdict.update({file_id : checksum})

    return processdict


@transact
def receiver_file_align(store, filesdict, processdict):
    """
    This function is called when the single InternalFile has been processed,
    they became aligned respect the Delivery specification of the node.
    """
    receiverfile_list = []

    for internalfile_id in filesdict.iterkeys():

        ifile = store.find(InternalFile, InternalFile.id == unicode(internalfile_id)).one()
        ifile.sha2sum = unicode(processdict.get(internalfile_id))

        receiverfilen = 0
        for receiver in ifile.internaltip.receivers:
            log.msg("ReceiverFile creation for user %s, file %s"
                    % (receiver.name, ifile.name) )

            receiverfile = ReceiverFile()
            receiverfile.downloads = 0
            receiverfile.receiver_id = receiver.id
            receiverfile.internalfile_id = ifile.id
            receiverfile.internaltip_id = ifile.internaltip.id

            # the lines below are copyed / tested in test_gpg.py
            if receiver.gpg_key_status == Receiver._gpg_types[1] and receiver.gpg_enable_files:
                try:
                    received_desc = admin_serialize_receiver(receiver)
                    gpoj = GLBGPG(received_desc)
                    gpoj.validate_key(received_desc['gpg_key_armor'])
                    encrypted_file_path = gpoj.encrypt_file(ifile.file_path, )
                    gpoj.destroy_environment()

                    log.debug("Generated encrypted version of %s for %s in %s" % (
                        ifile.name, receiver.username, encrypted_file_path ))

                    receiverfile.file_path = encrypted_file_path
                except Exception as excep:
                    log.err("Error when encrypting %s for %s: %s" % (
                        ifile.name, receiver.username, excep.message
                    ))
                    # In this case, fallback in plain text, or what ? I say fallback
                    # has to be an option but not be the default, or would
                    # act as a protocol downgrade attack vector.
            else:
                receiverfile.file_path = ifile.file_path

            receiverfile.mark = ReceiverFile._marker[0] # not notified

            store.add(receiverfile)
            store.commit()
            receiverfile_list.append(receiverfile.id)
            receiverfilen += 1

        log.debug("Generated ReceiverFile (%d) from %s [%s] and updated with checksum %s"
                % (receiverfilen, ifile.id, ifile.name, ifile.sha2sum))

        # can be extended processing in the future, here
        ifile.mark = InternalFile._marker[1] # Ready

    return receiverfile_list


def create_receivertip(store, receiver, internaltip, tier):
    """
    Create ReceiverTip for the required tier of Receiver.
    """
    # receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
    log.debug('Creating ReceiverTip for: %s (level %d in request %d)'
            % (receiver.name, receiver.receiver_level, tier))

    if receiver.receiver_level != tier:
        return

    receivertip = ReceiverTip()
    receivertip.internaltip_id = internaltip.id
    receivertip.access_counter = 0
    receivertip.expressed_pertinence = 0
    receivertip.receiver_id = receiver.id
    receivertip.mark = ReceiverTip._marker[0]
    store.add(receivertip)

    log.debug('Created! [/#/status/%s]' % receivertip.id)

    return receivertip.id


@transact
def tip_creation(store):
    """
    look for all the finalized InternalTip, create ReceiverTip for the
    first tier of Receiver, and shift the marker in 'first' aka di,ostron.zo
    """
    created_rtip = []

    finalized = store.find(InternalTip, InternalTip.mark == InternalTip._marker[1])

    for internaltip in finalized:

        for receiver in internaltip.receivers:
            rtip_id = create_receivertip(store, receiver, internaltip, 1)

            created_rtip.append(rtip_id)

        internaltip.mark = internaltip._marker[2]

    return created_rtip

    # update below with the return_dict
    #promoted = store.find(InternalTip,
    #                    ( InternalTip.mark == InternalTip._marker[2],
    #                      InternalTip.pertinence_counter >= InternalTip.escalation_threshold ) )

    #for internaltip in promoted:
    #    for receiver in internaltip.receivers:
    #        rtip_id = create_receivertip(store, receiver, internaltip, 2)
    #        created_tips.append(rtip_id)
    #
    #    internaltip.mark = internaltip._marker[3]


class APSDelivery(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is process/validate the files, compute checksum, and
        apply the delivery method configured.
        """
        try:
            # ==> Submission && Escalation
            info_created_tips = yield tip_creation()
            if info_created_tips:
                log.debug("Delivery job: created %d tips" % len(info_created_tips))

            # ==> Files && Files update
            filesdict = yield file_preprocess()
            # return a dict { "file_uuid" : "file_path" }

            if filesdict:
                log.debug("Delivery job: parsing %d new files" % len(filesdict))

                # compute checksum, processing the file on the disk ( outside the transactions)
                processdict = file_process(filesdict)
                # return a dict { "file_uuid" : checksum }

                yield receiver_file_align(filesdict, processdict)

        except Exception as excep:
            log.err("Exception in asyncronous delivery job: %s" % excep )
            sys.excepthook(*sys.exc_info())
