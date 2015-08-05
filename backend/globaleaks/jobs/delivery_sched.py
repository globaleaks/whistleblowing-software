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
import sys

import os
from twisted.internet.defer import inlineCallbacks
from globaleaks.jobs.base import GLJob
from globaleaks.models import InternalFile, InternalTip, ReceiverTip, \
                              ReceiverFile
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.utils.utility import log
from globaleaks.security import GLBPGP, GLSecureFile
from globaleaks.handlers.admin import admin_serialize_receiver


__all__ = ['DeliverySchedule']


def serialize_internalfile(ifile):
    ifile_dict = {
        'id': ifile.id,
        'internaltip_id': ifile.internaltip_id,
        'name': ifile.name,
        'file_path': ifile.file_path,
        'content_type': ifile.content_type,
        'size': ifile.size,
    }

    return ifile_dict

def serialize_receiverfile(rfile):
    rfile_dict = {
        'id' : rfile.id,
        'internaltip_id': rfile.internaltip_id,
        'internalfile_id': rfile.internalfile_id,
        'receiver_id': rfile.receiver_id,
        'receivertip_id': rfile.receivertip_id,
        'file_path': rfile.file_path,
        'size': rfile.size,
        'downloads': rfile.downloads,
        'last_access': rfile.last_access,
        'status': rfile.status,
    }

    return rfile_dict

@transact_ro
def get_files_by_itip(store, itip_id):
    ifiles = store.find(InternalFile, InternalFile.internaltip_id == unicode(itip_id))

    ifile_list = []
    for ifil in ifiles:
        ifile_list.append(serialize_internalfile(ifil))

    return ifile_list


@transact_ro
def get_receiverfile_by_itip(store, itip_id):
    rfiles = store.find(ReceiverFile, ReceiverFile.internaltip_id == unicode(itip_id))

    rfile_list = []
    for rfile in rfiles:
        rfile_list.append(serialize_receiverfile(rfile))

    return rfile_list


@transact
def receiverfile_planning(store):
    """
    This function roll over the InternalFile uploaded, extract a path, id and
    receivers associated, one entry for each combination. representing the
    ReceiverFile that need to be created.
    """
    receiverfiles_maps = {}

    ifiles = store.find(InternalFile, InternalFile.new == True)

    for ifile in ifiles:
        if (ifile.processing_attempts >= 3):
            log.err("")
            ifile.new = False
            continue

        elif (ifile.processing_attempts > 1):
            log.debug("")

        ifile.processing_attepts = ifile.processing_attempts + 1

        for receiver in ifile.internaltip.receivers:
            rtrf = store.find(ReceiverTip, ReceiverTip.internaltip_id == ifile.internaltip_id,
                              ReceiverTip.receiver_id == receiver.id).one()

            receiverfile = ReceiverFile()
            receiverfile.receiver_id = receiver.id
            receiverfile.internaltip_id = ifile.internaltip_id
            receiverfile.internalfile_id = ifile.id
            receiverfile.receivertip_id = rtrf.id
            receiverfile.file_path = ifile.file_path
            receiverfile.size = ifile.size
            receiverfile.status = u'processing'

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
                'status': u'processing',
                'path': ifile.file_path,
                'size': ifile.size,
                'receiver': admin_serialize_receiver(receiver, GLSetting.memory_copy.language)
            })

    return receiverfiles_maps


def fsops_pgp_encrypt(fpath, recipient_pgp):
    """
    return
        path of encrypted file,
        length of the encrypted file

    this function is used to encrypt a file for a specific recipient.
    commonly 'receiver_desc' is expected as second argument;
    anyhow a simpler dict can be used.

    required keys are checked on top

    """
    gpoj = GLBPGP()

    try:
        gpoj.load_key(recipient_pgp['pgp_key_public'])

        filepath = os.path.join(GLSetting.submission_path, fpath)

        with GLSecureFile(filepath) as f:
            encrypted_file_path, encrypted_file_size = \
                gpoj.encrypt_file(recipient_pgp['pgp_key_fingerprint'], filepath, f, GLSetting.submission_path)
    except:
        raise

    finally:
        # the finally statement is always called also if
        # except contains a return or a raise
        gpoj.destroy_environment()

    return encrypted_file_path, encrypted_file_size


def process_files(receiverfiles_maps):
    """
    @param receiverfiles_maps: the mapping of ifile/rfiles to be created on filesystem
    @return: return None
    """
    for ifile_id, receiverfiles_map in receiverfiles_maps.iteritems():
        ifile_path = receiverfiles_map['ifile_path']
        ifile_name = os.path.basename(ifile_path).split('.')[0]
        plain_path = os.path.join(GLSetting.submission_path, "%s.plain" % ifile_name)

        receiverfiles_map['plaintext_file_needed'] = False
        for rcounter, rfileinfo in enumerate(receiverfiles_map['rfiles']):
            if rfileinfo['receiver']['pgp_key_status'] == u'enabled':
                try:
                    new_path, new_size = fsops_pgp_encrypt(rfileinfo['path'], rfileinfo['receiver'])

                    log.debug("%d# Switch on Receiver File for %s path %s => %s size %d => %d" %
                              (rcounter,  rfileinfo['receiver']['name'], rfileinfo['path'],
                               new_path, rfileinfo['size'], new_size))

                    rfileinfo['path'] = new_path
                    rfileinfo['size'] = new_size
                    rfileinfo['status'] = u'encrypted'
                except Exception as excep:
                    log.err("%d# Unable to complete PGP encrypt for %s on %s: %s. marking the file as unavailable." % (
                            rcounter, rfileinfo['receiver']['name'], rfileinfo['path'], excep)
                    )
                    rfileinfo['status'] = u'unavailable'
            elif GLSetting.memory_copy.allow_unencrypted:
                receiverfiles_map['plaintext_file_needed'] = True
                rfileinfo['status'] = u'reference'
                rfileinfo['path'] = plain_path
            else:
                rfileinfo['status'] = u'nokey'

        if receiverfiles_map['plaintext_file_needed']:
            log.debug(":( NOT all receivers support PGP and the system allows plaintext version of files: %s saved as plaintext file %s" %
                      (ifile_path, plain_path))

            try:
                with open(plain_path, "wb") as plaintext_f, GLSecureFile(ifile_path) as encrypted_file:
                    chunk_size = 4096
                    written_size = 0
                    while True:
                        chunk = encrypted_file.read(chunk_size)
                        if len(chunk) == 0:
                            if written_size != receiverfiles_map['ifile_size']:
                                log.err("Integrity error on rfile write for ifile %s; ifile_size(%d), rfile_size(%d)" %
                                        (ifile_id, receiverfiles_map['ifile_path'], receiverfiles_map['ifile_size']))
                            break
                        written_size += len(chunk)
                        plaintext_f.write(chunk)

                receiverfiles_map['ifile_path'] = plain_path
            except Exception as excep:
                log.err("Unable to create plaintext file %s: %s" % (plain_path, excep))
        else:
            log.debug("All Receivers support PGP or the system denies plaintext version of files: marking internalfile as removed")

        # the original AES file should always be deleted
        log.debug("Deleting the submission AES encrypted file: %s" % ifile_path)

        # Remove the AES file
        try:
            os.remove(ifile_path)
        except OSError as ose:
            log.err("Unable to remove %s: %s" % (ifile_path, ose.message))

        # Remove the AES file key
        try:
            os.remove(os.path.join(GLSetting.ramdisk_path, ("%s%s" % (GLSetting.AES_keyfile_prefix, ifile_name))))
        except OSError as ose:
            log.err("Unable to remove keyfile associated with %s: %s" % (ifile_path, ose.message))


@transact
def update_internalfile_and_store_receiverfiles(store, receiverfiles_maps):
    for ifile_id, receiverfiles_map in receiverfiles_maps.iteritems():
        ifile = None
        try:
            ifile = store.find(InternalFile,
                               InternalFile.id == ifile_id).one()
        except Exception as excep:
            log.err("Error in find %s: %s" % (ifile_id, excep.message))
            continue

        if ifile is None:
            continue

        ifile.new = False

        for rf in receiverfiles_map['rfiles']:
            rfile = None
            try:
                rfile = store.find(ReceiverFile,
                                   ReceiverFile.id == rf['id']).one()

            except Exception as excep:
                log.err("Error in find %s: %s" % (file_path, excep.message))
                continue

            if rfile is None:
                continue

            rfile.status = rf['status']
            rfile.file_path = rf['path']
            rfile.size = rf['size']

        # update filepath possibly changed in case of plaintext file needed
        ifile.file_path = receiverfiles_map['ifile_path']


class DeliverySchedule(GLJob):
    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to process/validate files, compute their checksums and
        apply the configured delivery method.
        """
        receiverfiles_maps = yield receiverfile_planning()

        if len(receiverfiles_maps) == 0:
            return

        process_files(receiverfiles_maps)

        yield update_internalfile_and_store_receiverfiles(receiverfiles_maps)
