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
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalFile, ReceiverFile, ReceiverTip
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import send_exception_email
from globaleaks.utils.utility import log
from globaleaks.security import GLSecureFile
from globaleaks.handlers.admin.receiver import admin_serialize_receiver


__all__ = ['DeliverySchedule']


INTERNALFILES_HANDLE_RETRY_MAX = 3


@transact
def receiverfile_planning(store):
    """
    This function roll over the InternalFile uploaded, extract a path, id and
    receivers associated, one entry for each combination. representing the
    ReceiverFile that need to be created.
    """
    receiverfiles_maps = {}

    for ifile in store.find(InternalFile, InternalFile.new == True):
        if ifile.processing_attempts >= INTERNALFILES_HANDLE_RETRY_MAX:
            ifile.new = False
            error = "Failed to handle receiverfiles creation for ifile %s (%d retries)" % \
                    (ifile.id, INTERNALFILES_HANDLE_RETRY_MAX)
            log.err(error)
            send_exception_email(error)
            continue

        elif ifile.processing_attempts >= 1:
            log.err("Failed to handle receiverfiles creation for ifile %s (retry %d/%d)" %
                    (ifile.id, ifile.processing_attempts, INTERNALFILES_HANDLE_RETRY_MAX))

        
        if ifile.processing_attempts:
            log.debug("Starting handling receiverfiles creation for ifile %s retry %d/%d" %
                  (ifile.id, ifile.processing_attempts, INTERNALFILES_HANDLE_RETRY_MAX))

        ifile.processing_attempts += 1

        for rtip in ifile.internaltip.receivertips:
            receiverfile = ReceiverFile()
            receiverfile.receiver_id = rtip.receiver.id
            receiverfile.internaltip_id = ifile.internaltip_id
            receiverfile.internalfile_id = ifile.id
            receiverfile.receivertip_id = rtip.id
            receiverfile.file_path = ifile.file_path
            receiverfile.size = ifile.size
            receiverfile.status = u'processing'

            # https://github.com/globaleaks/GlobaLeaks/issues/444
            # avoid to mark the receiverfile as new if it is part of a submission
            # this way we avoid to send unuseful messages
            receiverfile.new = False if ifile.submission else True

            store.add(receiverfile)

            if ifile.id not in receiverfiles_maps:
                receiverfiles_maps[ifile.id] = {
                  'plaintext_file_needed': False,
                  'ifile_id': ifile.id,
                  'ifile_path': ifile.file_path,
                  'ifile_size': ifile.size,
                  'rfiles': []
                }

            receiverfiles_maps[ifile.id]['rfiles'].append({
                'id': receiverfile.id,
                'status': receiverfile.status,
                'path': ifile.file_path,
                'size': ifile.size,
                'receiver': admin_serialize_receiver(rtip.receiver, GLSettings.memory_copy.default_language)
            })

    return receiverfiles_maps


def process_files(receiverfiles_maps):
    """
    @param receiverfiles_maps: the mapping of ifile/rfiles to be created on filesystem
    @return: return None
    """
    for ifile_id, receiverfiles_map in receiverfiles_maps.iteritems():
        ifile_path = receiverfiles_map['ifile_path']
        ifile_name = os.path.basename(ifile_path).split('.')[0]
        destination_path = os.path.join(GLSettings.submission_path, "%s" % ifile_name)
        file_size = 0

        try:
            with GLSecureFile(ifile_path) as encrypted_file, open(destination_path, "wb") as destination_file:
                chunk_size = 4096
                while 1:
                    chunk = encrypted_file.read(chunk_size)
                    if len(chunk) <= 0:
                        break

                    file_size += len(chunk)
                    destination_file.write(chunk)
        finally:
            GLSecureFile.remove(ifile_path)

        for rfileinfo in receiverfiles_map['rfiles']:
            rfileinfo['path'] = destination_path
            rfileinfo['size'] = file_size
            rfileinfo['status'] = 'bcrypto'


@transact
def update_internalfile_and_store_receiverfiles(store, receiverfiles_maps):
    for ifile_id, receiverfiles_map in receiverfiles_maps.iteritems():
        ifile = store.find(InternalFile, InternalFile.id == ifile_id).one()
        if ifile is None:
            continue

        ifile.new = False

        # update filepath possibly changed in case of plaintext file needed
        ifile.file_path = receiverfiles_map['ifile_path']

        for rf in receiverfiles_map['rfiles']:
            rfile = store.find(ReceiverFile, ReceiverFile.id == rf['id']).one()
            if rfile is None:
                continue

            rfile.file_path = rf['path']
            rfile.size = rf['size']


class DeliverySchedule(GLJob):
    name = "Delivery"
    monitor_time = 1800

    @inlineCallbacks
    def operation(self):
        receiverfiles_maps = yield receiverfile_planning()

        if len(receiverfiles_maps):
            process_files(receiverfiles_maps)
            yield update_internalfile_and_store_receiverfiles(receiverfiles_maps)
