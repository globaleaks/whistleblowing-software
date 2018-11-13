# -*- coding: utf-8 -*-
import os

from twisted.internet import abstract
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact
from globaleaks.utils.crypto import generateRandomKey, GCE
from globaleaks.utils.pgp import PGPContext
from globaleaks.settings import Settings
from globaleaks.utils.log import log

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
                              .filter(models.InternalFile.new == True,
                                      models.InternalTip.id == models.InternalFile.internaltip_id):
        ifile.new = False
        for rtip, user in session.query(models.ReceiverTip, models.User) \
                                 .filter(models.ReceiverTip.internaltip_id == ifile.internaltip_id,
                                         models.User.id == models.ReceiverTip.receiver_id):
            receiverfile = models.ReceiverFile()
            receiverfile.internalfile_id = ifile.id
            receiverfile.receivertip_id = rtip.id
            receiverfile.filename = ifile.filename
            receiverfile.status = u'processing'

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
                  'plaintext_file_needed': False,
                  'rfiles': [],
                }

            receiverfiles_maps[ifile.id]['rfiles'].append({
                'id': receiverfile.id,
                'status': receiverfile.status,
                'filename': ifile.filename,
                'size': ifile.size,
                'receiver': {
                    'name': user.name,
                    'pgp_key_public': user.pgp_key_public,
                    'pgp_key_fingerprint': user.pgp_key_fingerprint,
                },
            })

    for wbfile, itip in session.query(models.WhistleblowerFile, models.InternalTip)\
                                .filter(models.WhistleblowerFile.new == True,
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
            while True:
                chunk = encrypted_file.read(abstract.FileDescriptor.bufferSize)
                if not chunk:
                    break
                plaintext_file.write(chunk)

    except Exception as excep:
        log.err("Unable to create plaintext file %s: %s", dest_path, excep)


def write_encrypted_file(key, sf, dest_path):
    try:
        with sf.open('rb') as encrypted_file, \
             GCE.streaming_encryption_open('ENCRYPT', key, dest_path) as seo:
            chunk = encrypted_file.read(abstract.FileDescriptor.bufferSize)
            while (True):
                x = encrypted_file.read(abstract.FileDescriptor.bufferSize)
                if not x:
                    seo.encrypt_chunk(chunk, 1)
                    break

                seo.encrypt_chunk(chunk, 0)

                chunk = x
    except Exception as excep:
        log.err("Unable to create plaintext file %s: %s", dest_path, excep)


def process_receiverfiles(state, receiverfiles_maps):
    """
    @param receiverfiles_maps: the mapping of ifile/rfiles to be created on filesystem
    @return: return None
    """
    for id, receiverfiles_map in receiverfiles_maps.items():
        key = receiverfiles_map['crypto_tip_pub_key']
        filename = receiverfiles_map['filename']
        filecode = filename.split('.')[0]
        plaintext_name = "%s.plain" % filecode
        encrypted_name = "%s.encrypted" % filecode
        pgp_name = "%s.encrypted" % filecode
        plaintext_path = os.path.abspath(os.path.join(Settings.attachments_path, plaintext_name))
        encrypted_path = os.path.abspath(os.path.join(Settings.attachments_path, encrypted_name))
        pgp_path = os.path.abspath(os.path.join(Settings.attachments_path, pgp_name))

        sf = state.get_tmp_file_by_name(filename)

        if key:
            receiverfiles_map['filename'] = encrypted_name
            write_encrypted_file(key, sf, encrypted_path)
            for rf in receiverfiles_map['rfiles']:
                rf['filename'] = encrypted_name
        else:
            for rcounter, rfileinfo in enumerate(receiverfiles_map['rfiles']):
                with sf.open('rb') as encrypted_file:
                    if rfileinfo['receiver']['pgp_key_public']:
                        try:
                            encrypt_file_with_pgp(state,
                                                  encrypted_file,
                                                  rfileinfo['receiver']['pgp_key_public'],
                                                  rfileinfo['receiver']['pgp_key_fingerprint'],
                                                  pgp_path)
                            rfileinfo['filename'] = pgp_path
                            rfileinfo['status'] = u'encrypted'
                        except Exception as excep:
                            log.err("%d# Unable to complete PGP encrypt for %s on %s: %s. marking the file as unavailable.",
                                    rcounter, rfileinfo['receiver']['name'], rfileinfo['filename'], excep)
                            rfileinfo['status'] = u'unavailable'
                    elif state.tenant_cache[receiverfiles_map['tid']].allow_unencrypted:
                        receiverfiles_map['plaintext_file_needed'] = True
                        rfileinfo['filename'] = plaintext_name
                        rfileinfo['status'] = u'reference'
                    else:
                        rfileinfo['status'] = u'nokey'

        if receiverfiles_map['plaintext_file_needed']:
            write_plaintext_file(sf, plaintext_path)


def process_whistleblowerfiles(state, whistleblowerfiles_maps):
    """
    @param whistleblowerfiles_maps: descriptos of whistleblower files to be processed
    @return: return None
    """
    for id, whistleblowerfiles_map in whistleblowerfiles_maps.items():
        key = whistleblowerfiles_map['crypto_tip_pub_key']
        filename = whistleblowerfiles_map['filename']
        filecode = filename.split('.')[0]
        plaintext_name = "%s.plain" % filecode
        encrypted_name = "%s.encrypted" % filecode
        plaintext_path = os.path.abspath(os.path.join(Settings.attachments_path, plaintext_name))
        encrypted_path = os.path.abspath(os.path.join(Settings.attachments_path, encrypted_name))

        sf = state.get_tmp_file_by_name(filename)

        if key:
            whistleblowerfiles_map['filename'] = encrypted_name
            write_encrypted_file(key, sf, encrypted_path)
        else:
            whistleblowerfiles_map['filename'] = plaintext_name
            write_plaintext_file(sf, plaintext_path)


@transact
def update_receiverfiles(session, receiverfiles_maps):
    for id, receiverfiles_map in receiverfiles_maps.items():
        ifile = session.query(models.InternalFile).filter(models.InternalFile.id == id).one_or_none()
        if ifile is None:
            continue

        ifile.new = False
        ifile.filename = receiverfiles_map['filename']

        for rf in receiverfiles_map['rfiles']:
            rfile = session.query(models.ReceiverFile).filter(models.ReceiverFile.id == rf['id']).one_or_none()
            if rfile is not None:
                rfile.status = rf['status']
                rfile.filename = rf['filename']


@transact
def update_whistleblowerfiles(session, whistleblowerfiles_maps):
    for id, whistleblowerfiles_map in whistleblowerfiles_maps.items():
        wbfile = session.query(models.WhistleblowerFile).filter(models.WhistleblowerFile.id == id).one_or_none()
        if wbfile is not None:
            wbfile.new = False
            wbfile.filename = whistleblowerfiles_map['filename']


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
