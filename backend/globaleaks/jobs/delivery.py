# -*- coding: utf-8 -*-
# Implements the delivery operations performed when a new submission
# is created, or a new file is append to an existing Tip. delivery
# works on the file and on the fields, not in the comments.
#
# Call also the FileProcess working point, in order to verify which
# kind of file has been submitted.
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact
from globaleaks.security import GLBPGP, SecureFile, generateRandomKey
from globaleaks.settings import Settings
from globaleaks.utils.utility import log

__all__ = ['Delivery']


INTERNALFILES_HANDLE_RETRY_MAX = 3


@transact
def receiverfile_planning(store):
    """
    This function roll over the InternalFile uploaded, extract a path, id and
    receivers associated, one entry for each combination. representing the
    ReceiverFile that need to be created.
    """
    receiverfiles_maps = {}

    for ifile in store.find(models.InternalFile, new=True).order_by(models.InternalFile.creation_date):
        if ifile.processing_attempts >= INTERNALFILES_HANDLE_RETRY_MAX:
            ifile.new = False
            log.err("Failed to handle receiverfiles creation for ifile %s (%d retries)",
                    ifile.id, INTERNALFILES_HANDLE_RETRY_MAX)
            continue

        elif ifile.processing_attempts >= 1:
            log.err("Failed to handle receiverfiles creation for ifile %s (retry %d/%d)",
                    ifile.id, ifile.processing_attempts, INTERNALFILES_HANDLE_RETRY_MAX)


        if ifile.processing_attempts:
            log.debug("Starting handling receiverfiles creation for ifile %s retry %d/%d",
                      ifile.id, ifile.processing_attempts, INTERNALFILES_HANDLE_RETRY_MAX)

        ifile.processing_attempts += 1

        for rtip, user in store.find((models.ReceiverTip, models.User),
                                     models.ReceiverTip.internaltip_id == ifile.internaltip_id,
                                     models.User.id == models.ReceiverTip.receiver_id):
            receiverfile = models.ReceiverFile()
            receiverfile.tid = rtip.tid
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
                  'rfiles': [],
                  'tid': rtip.tid,
                }

            receiverfiles_maps[ifile.id]['rfiles'].append({
                'id': receiverfile.id,
                'status': u'processing',
                'path': ifile.file_path,
                'size': ifile.size,
                'receiver': {
                    'name': user.name,
                    'pgp_key_public': user.pgp_key_public,
                    'pgp_key_fingerprint': user.pgp_key_fingerprint,
                },
            })

    return receiverfiles_maps


def fsops_pgp_encrypt(state, fpath, key, fingerprint):
    """
    Encrypt the file for a speficic key

    return
        path of encrypted file,
        length of the encrypted file
    """
    gpoj = GLBPGP()

    try:
        gpoj.load_key(key)

        filepath = os.path.join(state.settings.attachments_path, fpath)

        with SecureFile(filepath) as f:
            encrypted_file_path = os.path.join(os.path.abspath(state.settings.attachments_path), "pgp_encrypted-%s" % generateRandomKey(16))
            _, encrypted_file_size = gpoj.encrypt_file(fingerprint, f, encrypted_file_path)

    except:
        raise

    finally:
        # the finally statement is always called also if
        # except contains a return or a raise
        gpoj.destroy_environment()

    return encrypted_file_path, encrypted_file_size


def process_files(state, receiverfiles_maps):
    """
    @param receiverfiles_maps: the mapping of ifile/rfiles to be created on filesystem
    @return: return None
    """
    for ifile_id, receiverfiles_map in receiverfiles_maps.items():
        ifile_path = receiverfiles_map['ifile_path']
        ifile_name = os.path.basename(ifile_path).split('.')[0]
        plain_path = os.path.join(Settings.attachments_path, "%s.plain" % ifile_name)

        receiverfiles_map['plaintext_file_needed'] = False
        for rcounter, rfileinfo in enumerate(receiverfiles_map['rfiles']):
            if rfileinfo['receiver']['pgp_key_public']:
                try:
                    new_path, new_size = fsops_pgp_encrypt(state,
                                                           rfileinfo['path'],
                                                           rfileinfo['receiver']['pgp_key_public'],
                                                           rfileinfo['receiver']['pgp_key_fingerprint'])

                    log.debug("%d# Switch on Receiver File for %s path %s => %s size %d => %d",
                              rcounter,  rfileinfo['receiver']['name'], rfileinfo['path'],
                              new_path, rfileinfo['size'], new_size)

                    rfileinfo['path'] = new_path
                    rfileinfo['size'] = new_size
                    rfileinfo['status'] = u'encrypted'
                except Exception as excep:
                    log.err("%d# Unable to complete PGP encrypt for %s on %s: %s. marking the file as unavailable.",
                            rcounter, rfileinfo['receiver']['name'], rfileinfo['path'], excep)
                    rfileinfo['status'] = u'unavailable'
            elif state.tenant_cache[receiverfiles_map['tid']].allow_unencrypted:
                receiverfiles_map['plaintext_file_needed'] = True
                rfileinfo['status'] = u'reference'
                rfileinfo['path'] = plain_path
            else:
                rfileinfo['status'] = u'nokey'

        if receiverfiles_map['plaintext_file_needed']:
            log.debug("Not all receivers support PGP and the system allows plaintext version of files: %s saved as plaintext file %s",
                      ifile_path, plain_path)

            try:
                with open(plain_path, "wb") as plaintext_f, SecureFile(ifile_path) as encrypted_file:
                    chunk_size = 4096
                    written_size = 0
                    while True:
                        chunk = encrypted_file.read(chunk_size)
                        if not chunk:
                            if written_size != receiverfiles_map['ifile_size']:
                                log.err("Integrity error on rfile write for ifile %s; ifile_size(%d), rfile_size(%d)",
                                        ifile_id, receiverfiles_map['ifile_size'], written_size)
                            break
                        written_size += len(chunk)
                        plaintext_f.write(chunk)

                receiverfiles_map['ifile_path'] = plain_path
            except Exception as excep:
                log.err("Unable to create plaintext file %s: %s", plain_path, excep)
        else:
            log.debug("All receivers support PGP or the system denies plaintext version of files: marking internalfile as removed")

        # the original AES file should always be deleted
        log.debug("Deleting the submission AES encrypted file: %s", ifile_path)

        # Remove the AES file
        try:
            os.remove(ifile_path)
        except OSError as ose:
            log.err("Unable to remove %s: %s", ifile_path, ose.strerror)

        # Remove the AES file key
        try:
            os.remove(os.path.join(state.settings.ramdisk_path, ("%s%s" % (state.settings.AES_keyfile_prefix, ifile_name))))
        except OSError as ose:
            log.err("Unable to remove keyfile associated with %s: %s", ifile_path, ose.strerror)


@transact
def update_internalfile_and_store_receiverfiles(store, receiverfiles_maps):
    for ifile_id, receiverfiles_map in receiverfiles_maps.items():
        ifile = store.find(models.InternalFile, models.InternalFile.id == ifile_id).one()
        if ifile is None:
            continue

        ifile.new = False

        # update filepath possibly changed in case of plaintext file needed
        ifile.file_path = receiverfiles_map['ifile_path']

        for rf in receiverfiles_map['rfiles']:
            rfile = store.find(models.ReceiverFile, models.ReceiverFile.id == rf['id']).one()
            if rfile is None:
                continue

            rfile.status = rf['status']
            rfile.file_path = rf['path']
            rfile.size = rf['size']


class Delivery(LoopingJob):
    interval = 5
    monitor_interval = 180

    @inlineCallbacks
    def operation(self):
        """
        This function creates receiver files
        """
        receiverfiles_maps = yield receiverfile_planning()
        if receiverfiles_maps:
            process_files(self.state, receiverfiles_maps)
            yield update_internalfile_and_store_receiverfiles(receiverfiles_maps)
