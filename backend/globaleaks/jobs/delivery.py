# -*- coding: utf-8 -*-
import os

from twisted.internet import abstract
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs.job import LoopingJob
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.utils.crypto import generateRandomKey, GCE
from globaleaks.utils.log import log
from globaleaks.utils.pgp import PGPContext

__all__ = ['Delivery']


@transact
def file_delivery_planning(session):
    """
    This function roll over the InternalFile uploaded, extract a path, id and
    receivers associated, one entry for each combination. representing the
    ReceiverFile that need to be created.
    """
    receiverfiles_maps = {}
    whistleblowerfiles_maps = {}

    for ifile, itip in session.query(models.InternalFile, models.InternalTip)\
                              .filter(models.InternalFile.new.is_(True),
                                      models.InternalTip.id == models.InternalFile.internaltip_id):
        ifile.new = False
        for rtip, user in session.query(models.ReceiverTip, models.User) \
                                 .filter(models.ReceiverTip.internaltip_id == ifile.internaltip_id,
                                         models.User.id == models.ReceiverTip.receiver_id):
            receiverfile = models.ReceiverFile()
            receiverfile.internalfile_id = ifile.id
            receiverfile.receivertip_id = rtip.id
            receiverfile.filename = ifile.filename
            receiverfile.status = 'processing'

            # https://github.com/globaleaks/GlobaLeaks/issues/444
            # avoid to mark the receiverfile as new if it is part of a submission
            # this way we avoid to send unuseful messages
            receiverfile.new = not ifile.submission

            session.add(receiverfile)

            session.flush()

            if ifile.id not in receiverfiles_maps:
                receiverfiles_maps[ifile.id] = {
                    'tid': user.tid,
                    'crypto_tip_pub_key': itip.crypto_tip_pub_key,
                    'id': ifile.id,
                    'filename': ifile.filename,
                    'pgp_encrypted_for_everybody': True,
                    'rfiles': [],
                }

            receiverfiles_maps[ifile.id]['rfiles'].append({
                'id': receiverfile.id,
                'status': receiverfile.status,
                'filename': '',
                'status': 'reference',
                'size': ifile.size,
                'receiver': {
                    'name': user.name,
                    'pgp_key_public': user.pgp_key_public,
                    'pgp_key_fingerprint': user.pgp_key_fingerprint,
                },
            })

    for wbfile, itip in session.query(models.WhistleblowerFile, models.InternalTip)\
                               .filter(models.WhistleblowerFile.new.is_(True),
                                       models.ReceiverTip.id == models.WhistleblowerFile.receivertip_id,
                                       models.InternalTip.id == models.ReceiverTip.internaltip_id):

        wbfile.new = False
        whistleblowerfiles_maps[wbfile.id] = {
            'crypto_tip_pub_key': itip.crypto_tip_pub_key,
            'id': wbfile.id,
            'filename': wbfile.filename,
        }

    return receiverfiles_maps, whistleblowerfiles_maps


def encrypt_file_with_pgp(state, fd, key, fingerprint, dest_path):
    """
    Encrypt the file for a specific key
    """
    pgpctx = PGPContext(state.settings.tmp_path)

    pgpctx.load_key(key)

    pgpctx.encrypt_file(fingerprint, fd, dest_path)


def write_plaintext_file(sf, dest_path):
    try:
        with sf.open('rb') as encrypted_file, open(dest_path, "a+b") as plaintext_file:
            chunk = encrypted_file.read(abstract.FileDescriptor.bufferSize)
            while chunk:
                plaintext_file.write(chunk)
                chunk = encrypted_file.read(abstract.FileDescriptor.bufferSize)

    except Exception as excep:
        log.err("Unable to create plaintext file %s: %s", dest_path, excep)


def write_encrypted_file(key, sf, dest_path):
    try:
        with sf.open('rb') as encrypted_file, \
             GCE.streaming_encryption_open('ENCRYPT', key, dest_path) as seo:
            chunk = encrypted_file.read(abstract.FileDescriptor.bufferSize)
            while chunk:
                seo.encrypt_chunk(chunk, 0)
                chunk = encrypted_file.read(abstract.FileDescriptor.bufferSize)

            seo.encrypt_chunk(b'', 1)
    except Exception as excep:
        log.err("Unable to create plaintext file %s: %s", dest_path, excep)


def process_receiverfiles(state, files_maps):
    """
    Function that process uploaded receiverfiles

    :param state: A reference to the application state
    :param files_maps: descriptos of whistleblower files to be processed
    """
    for _, receiverfiles_map in files_maps.items():
        key = receiverfiles_map['crypto_tip_pub_key']
        filename = receiverfiles_map['filename']
        filecode = filename.split('.')[0]
        plaintext_name = "%s.plain" % filecode
        encrypted_name = "%s.encrypted" % filecode
        plaintext_path = os.path.abspath(os.path.join(Settings.attachments_path, plaintext_name))
        encrypted_path = os.path.abspath(os.path.join(Settings.attachments_path, encrypted_name))

        receiverfiles_map['filename'] = encrypted_name if key else plaintext_name

        sf = state.get_tmp_file_by_name(filename)

        for rcounter, rf in enumerate(receiverfiles_map['rfiles']):
            if key:
                rf['filename'] = encrypted_name
            else:
                rf['filename'] = plaintext_path

            try:
                with sf.open('rb') as encrypted_file:
                    if not rf['receiver']['pgp_key_public']:
                        receiverfiles_map['pgp_encrypted_for_everybody'] = False
                        continue

                    pgp_name = "%s.pgp" % generateRandomKey()
                    pgp_path = os.path.abspath(os.path.join(Settings.attachments_path, pgp_name))
                    encrypt_file_with_pgp(state,
                                          encrypted_file,
                                          rf['receiver']['pgp_key_public'],
                                          rf['receiver']['pgp_key_fingerprint'],
                                          pgp_path)
                    rf['filename'] = pgp_name
                    rf['status'] = 'encrypted'

            except Exception as excep:
                log.err("%d# Unable to complete PGP encrypt for %s on %s: %s. marking the file as unavailable.",
                        rcounter, rf['receiver']['name'], rf['filename'], excep)
                rf['status'] = 'unavailable'

        if not receiverfiles_map['pgp_encrypted_for_everybody']:
            if key:
                write_encrypted_file(key, sf, encrypted_path)
            else:
                write_plaintext_file(sf, plaintext_path)


def process_whistleblowerfiles(state, files_maps):
    """
    Function that process uploaded whistleblowerfiles

    :param state: A reference to the application state
    :param files_maps: descriptos of whistleblower files to be processed
    """
    for _, whistleblowerfiles_map in files_maps.items():
        key = whistleblowerfiles_map['crypto_tip_pub_key']
        filename = whistleblowerfiles_map['filename']
        filecode = filename.split('.')[0]

        sf = state.get_tmp_file_by_name(filename)

        if key:
            whistleblowerfiles_map['filename'] = "%s.encrypted" % filecode
            write_encrypted_file(key, sf, os.path.abspath(os.path.join(Settings.attachments_path, whistleblowerfiles_map['filename'])))
        else:
            whistleblowerfiles_map['filename'] = "%s.plain" % filecode
            write_plaintext_file(sf, os.path.abspath(os.path.join(Settings.attachments_path, whistleblowerfiles_map['filename'])))


@transact
def update_receiverfiles(session, files_maps):
    for id, receiverfiles_map in files_maps.items():
        ifile = session.query(models.InternalFile).filter(models.InternalFile.id == id).update({'new': False, 'filename': receiverfiles_map['filename']})

        for rf in receiverfiles_map['rfiles']:
            session.query(models.ReceiverFile).filter(models.ReceiverFile.id == rf['id']).update({'status': rf['status'], 'filename': rf['filename']})


@transact
def update_whistleblowerfiles(session, files_maps):
    for id, whistleblowerfiles_map in files_maps.items():
        session.query(models.WhistleblowerFile).filter(models.WhistleblowerFile.id == id).update({'new': False, 'filename': whistleblowerfiles_map['filename']})

class Delivery(LoopingJob):
    interval = 5
    monitor_interval = 180

    @inlineCallbacks
    def operation(self):
        """
        This function creates receiver files
        """
        receiverfiles_maps, whistleblowerfiles_maps = yield file_delivery_planning()
        if receiverfiles_maps:
            process_receiverfiles(self.state, receiverfiles_maps)
            yield update_receiverfiles(receiverfiles_maps)

        if whistleblowerfiles_maps:
            process_whistleblowerfiles(self.state, whistleblowerfiles_maps)
            yield update_whistleblowerfiles(whistleblowerfiles_maps)
