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
from globaleaks.utils.pgp import PGPContext
from globaleaks.utils.security import generateRandomKey, overwrite_and_remove
from globaleaks.settings import Settings
from globaleaks.utils.utility import log

__all__ = ['Delivery']


INTERNALFILES_HANDLE_RETRY_MAX = 3


@transact
def receiverfile_planning(session):
    """
    This function roll over the InternalFile uploaded, extract a path, id and
    receivers associated, one entry for each combination. representing the
    ReceiverFile that need to be created.
    """
    receiverfiles_maps = {}

    for ifile in session.query(models.InternalFile).filter(models.InternalFile.new == True).order_by(models.InternalFile.creation_date):
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

        for rtip, user in session.query(models.ReceiverTip, models.User) \
                                 .filter(models.ReceiverTip.internaltip_id == ifile.internaltip_id,
                                         models.User.id == models.ReceiverTip.receiver_id):
            receiverfile = models.ReceiverFile()
            receiverfile.internalfile_id = ifile.id
            receiverfile.receivertip_id = rtip.id
            receiverfile.filename = ifile.filename
            receiverfile.size = ifile.size
            receiverfile.status = u'processing'

            # https://github.com/globaleaks/GlobaLeaks/issues/444
            # avoid to mark the receiverfile as new if it is part of a submission
            # this way we avoid to send unuseful messages
            receiverfile.new = False if ifile.submission else True

            session.add(receiverfile)

            session.flush()

            if ifile.id not in receiverfiles_maps:
                receiverfiles_maps[ifile.id] = {
                  'plaintext_file_needed': False,
                  'ifile_id': ifile.id,
                  'ifile_name': ifile.filename,
                  'ifile_size': ifile.size,
                  'rfiles': [],
                  'tid': user.tid,
                }

            receiverfiles_maps[ifile.id]['rfiles'].append({
                'id': receiverfile.id,
                'status': u'processing',
                'filename': ifile.filename,
                'size': ifile.size,
                'receiver': {
                    'name': user.name,
                    'pgp_key_public': user.pgp_key_public,
                    'pgp_key_fingerprint': user.pgp_key_fingerprint,
                },
            })

    return receiverfiles_maps


def fsops_pgp_encrypt(state, sf, key, fingerprint):
    """
    Encrypt the file for a speficic key

    return
        path of encrypted file,
        length of the encrypted file
    """
    pgpctx = PGPContext(state.settings.tmp_path)

    pgpctx.load_key(key)

    with sf.open('rb') as f:
        encrypted_file_path = os.path.abspath(os.path.join(state.settings.attachments_path, "pgp_encrypted-%s" % generateRandomKey(16)))
        _, encrypted_file_size = pgpctx.encrypt_file(fingerprint, f, encrypted_file_path)

    return os.path.basename(encrypted_file_path), encrypted_file_size


def process_files(state, receiverfiles_maps):
    """
    @param receiverfiles_maps: the mapping of ifile/rfiles to be created on filesystem
    @return: return None
    """
    for ifile_id, receiverfiles_map in receiverfiles_maps.items():
        ifile_name = receiverfiles_map['ifile_name']
        plain_name = "%s.plain" % ifile_name.split('.')[0]
        plain_path = os.path.abspath(os.path.join(Settings.attachments_path, plain_name))

        sf = state.get_tmp_file_by_name(ifile_name)

        receiverfiles_map['plaintext_file_needed'] = False
        for rcounter, rfileinfo in enumerate(receiverfiles_map['rfiles']):
            if rfileinfo['receiver']['pgp_key_public']:
                try:
                    new_filename, new_size = fsops_pgp_encrypt(state,
                                                               sf,
                                                               rfileinfo['receiver']['pgp_key_public'],
                                                               rfileinfo['receiver']['pgp_key_fingerprint'])

                    log.debug("%d# Switch on Receiver File for %s filename %s => %s size %d => %d",
                              rcounter,  rfileinfo['receiver']['name'], rfileinfo['filename'],
                              new_filename, rfileinfo['size'], new_size)

                    rfileinfo['filename'] = new_filename
                    rfileinfo['size'] = new_size
                    rfileinfo['status'] = u'encrypted'
                except Exception as excep:
                    log.err("%d# Unable to complete PGP encrypt for %s on %s: %s. marking the file as unavailable.",
                            rcounter, rfileinfo['receiver']['name'], rfileinfo['filename'], excep)
                    rfileinfo['status'] = u'unavailable'
            elif state.tenant_cache[receiverfiles_map['tid']].allow_unencrypted:
                receiverfiles_map['plaintext_file_needed'] = True
                rfileinfo['filename'] = plain_name
                rfileinfo['status'] = u'reference'
            else:
                rfileinfo['status'] = u'nokey'

        if receiverfiles_map['plaintext_file_needed']:
            log.debug("Not all receivers support PGP and the system allows plaintext version of files: %s saved as plaintext file %s",
                      ifile_name, plain_name)

            try:
                with sf.open('rb') as encrypted_file, open(plain_path, "a+b") as plaintext_file:
                    while True:
                        chunk = encrypted_file.read(4096)
                        if not chunk:
                            break
                        plaintext_file.write(chunk)

                receiverfiles_map['ifile_name'] = plain_name
            except Exception as excep:
                log.err("Unable to create plaintext file %s: %s", plain_path, excep)
        else:
            log.debug("All receivers support PGP or the system denies plaintext version of files: marking internalfile as removed")


@transact
def update_internalfile_and_store_receiverfiles(session, receiverfiles_maps):
    for ifile_id, receiverfiles_map in receiverfiles_maps.items():
        ifile = session.query(models.InternalFile).filter(models.InternalFile.id == ifile_id).one_or_none()
        if ifile is None:
            continue

        ifile.new = False

        # update filepath possibly changed in case of plaintext file needed
        ifile.filename = receiverfiles_map['ifile_name']

        for rf in receiverfiles_map['rfiles']:
            rfile = session.query(models.ReceiverFile).filter(models.ReceiverFile.id == rf['id']).one_or_none()
            if rfile is None:
                continue

            rfile.status = rf['status']
            rfile.filename = rf['filename']
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
