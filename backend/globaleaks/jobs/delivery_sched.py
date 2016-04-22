# -*- encoding: utf-8 -*-
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
from storm.expr import In
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact, transact_ro
from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalFile, ReceiverFile, ReceiverTip
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import send_exception_email
from globaleaks.utils.utility import log
from globaleaks.security import GLBPGP, GLSecureFile, generateRandomKey
from globaleaks.handlers.admin.receiver import admin_serialize_receiver
from globaleaks.handlers.submission import serialize_internalfile


__all__ = ['DeliverySchedule']


@transact_ro
def get_new_ifile_descriptors(store):
    new_ifiles = store.find(InternalFile, InternalFile.new == True)

    return [serialize_internalfile(ifile) for ifile in new_ifiles]


def process_files(ifiles_descs):
    for ifile_desc in ifiles_descs:
        src_path = ifile_desc['file_path']
        src_name = os.path.basename(src_path).split('.')[0]
        dst_path = os.path.join(GLSettings.submission_path, "%s.pgp" % src_name)

        try:
            with open(dst_path, "wb") as dst_file, GLSecureFile(src_path) as src_file:
                chunk_size = 1000000 # 1MB
                while True:
                    chunk = src_file.read(chunk_size)
                    if len(chunk) == 0:
                        break
                    dst_file.write(chunk)

            ifile_desc['file_path'] = dst_path
        except Exception as ose:
            log.err("Failure while creating %s out of aes encrypted %s" % (dst_path, src_path))
            pass

        finally:
            # the original AES file should always be deleted
            log.debug("Deleting the submission AES encrypted file: %s" % src_path)

            # Remove the AES file
            try:
                os.remove(src_path)
            except OSError as ose:
                log.err("Unable to remove %s: %s" % (src_path, ose.message))

            # Remove the AES file key
            try:
                os.remove(os.path.join(GLSettings.ramdisk_path, ("%s%s" % (GLSettings.AES_keyfile_prefix, src_name))))
            except OSError as ose:
                log.err("Unable to remove keyfile associated with %s: %s" % (src_path, ose.message))


@transact
def mark_ifiles_has_false_and_create_rfiles(store, ifiles_descs):
    """
    This function roll over the InternalFile uploaded, extract a path, id and
    receivers associated, one entry for each combination. representing the
    ReceiverFile that need to be created.
    """
    for ifile_desc in ifiles_descs:
        ifile = store.find(InternalFile, InternalFile.id == ifile_desc['id']).one()

        try:
            for receiver in ifile.internaltip.receivers:
                rtrf = store.find(ReceiverTip, ReceiverTip.internaltip_id == ifile.internaltip_id,
                                  ReceiverTip.receiver_id == receiver.id).one()

                receiverfile = ReceiverFile()
                receiverfile.receiver_id = receiver.id
                receiverfile.internaltip_id = ifile.internaltip_id
                receiverfile.internalfile_id = ifile.id
                receiverfile.receivertip_id = rtrf.id
                receiverfile.file_path = ifile_desc['file_path']
                receiverfile.size = ifile.size
                receiverfile.status = u'reference'

                # https://github.com/globaleaks/GlobaLeaks/issues/444
                # avoid to mark the receiverfile as new if it is part of a submission
                # this way we avoid to send unuseful messages
                receiverfile.new = False if ifile.submission else True

                store.add(receiverfile)

        except:
            pass

        finally:
            ifile.new = False
            ifile.file_path = ifile_desc['file_path']


class DeliverySchedule(GLJob):
    name = "Delivery"
    monitor_time = 1800

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to process/validate files, compute their checksums and
        apply the configured delivery method.
        """
        ifiles_descs = yield get_new_ifile_descriptors()

        if len(ifiles_descs):
            try:
                process_files(ifiles_descs)
            except:
                pass
            finally:
                yield mark_ifiles_has_false_and_create_rfiles(ifiles_descs)
