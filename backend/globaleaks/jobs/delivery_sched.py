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
from globaleaks.third_party.rstr import xeger


__all__ = ['DeliverySchedule']

def serialize_internalfile(ifile):
    ifile_dict = {
        'id': ifile.id,
        'internaltip_id' : ifile.internaltip_id,
        'name' : ifile.name,
        'file_path' : ifile.file_path,
        'content_type' : ifile.content_type,
        'size' : ifile.size,
    }

    return ifile_dict

@transact_ro
def get_files_by_itip(store, itip_id):
    try:
        ifiles = store.find(InternalFile, InternalFile.internaltip_id == unicode(itip_id))
    except Exception as excep:
        log.err("Unable to retrive InternalFile(s) from InternalTip! %s" % excep)
        return []

    ifile_list = []
    for ifil in ifiles:
        ifile_list.append(serialize_internalfile(ifil))

    return ifile_list


def serialize_receiverfile(rfile):
    rfile_dict = {
        'id' : rfile.id,
        'internaltip_id' : rfile.internaltip_id,
        'internalfile_id' : rfile.internalfile_id,
        'receiver_id' : rfile.receiver_id,
        'receivertip_id' : rfile.receivertip_id,
        'file_path' : rfile.file_path,
        'size' : rfile.size,
        'downloads' : rfile.downloads,
        'last_access' : rfile.last_access,
        'status' : rfile.status,
    }

    return rfile_dict

@transact_ro
def get_receiverfile_by_itip(store, itip_id):
    try:
        rfiles = store.find(ReceiverFile, ReceiverFile.internaltip_id == unicode(itip_id))
    except Exception as excep:
        log.err("Unable to retrive ReceiverFile(s) from InternalTip! %s" % excep)
        return []

    rfile_list = []
    for rfil in rfiles:
        rfile_list.append(serialize_receiverfile(rfil))

    return rfile_list


@transact
def receiverfile_planning(store):
    """
    This function roll over the InternalFile uploaded, extract a path, id and
    receivers associated, one entry for each combination. representing the
    ReceiverFile that need to be created.
    """
    ifilesmap = {}

    files = store.find(InternalFile, InternalFile.new == True)
    for filex in files:
        for receiver in filex.internaltip.receivers:
            if filex.file_path not in ifilesmap:
                ifilesmap[filex.file_path] = list()

            receiver_desc = admin_serialize_receiver(receiver, GLSetting.memory_copy.language)

            map_info = {
                'receiver' : receiver_desc,
                'path' : filex.file_path,
                'size' : filex.size,
                'status' : u'reference'
            }

            # AS KEY, file path is used to keep track of the original
            # path, because shall be renamed in .plaintext (in the unlucky case
            # of receivers without PGP)
            # AS FIELD, it can be replaced with a dedicated PGP encrypted path
            ifilesmap[filex.file_path].append(map_info)

        filex.new = False

    return ifilesmap


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

@transact
def receiverfile_create(store, if_path, recv_path, status, recv_size, receiver_desc):
    try:
        ifile = store.find(InternalFile, InternalFile.file_path == unicode(if_path)).one()

        if not ifile:
            log.err("InternalFile with path %s not found !?" % if_path)
            raise Exception("This is bad!")

        log.debug("ReceiverFile creation for user %s, '%s' bytes %d = %s)"
                % (receiver_desc['name'], ifile.name, recv_size, status ) )

        rtrf = store.find(ReceiverTip, ReceiverTip.internaltip_id == ifile.internaltip_id,
                          ReceiverTip.receiver_id == receiver_desc['id']).one()

        receiverfile = ReceiverFile()
        receiverfile.receiver_id = receiver_desc['id']
        receiverfile.internaltip_id = ifile.internaltip_id
        receiverfile.internalfile_id = ifile.id
        receiverfile.receivertip_id = rtrf.id
        receiverfile.file_path = unicode(recv_path)
        receiverfile.size = recv_size
        receiverfile.status = unicode(status)

        store.add(receiverfile)

    except Exception as excep:
        log.err("Error when saving ReceiverFile %s for '%s': %s" %
                (if_path, receiver_desc['name'], excep.message))


@transact
def do_final_internalfile_update(store, file_path, new_path):
    try:
        ifile = store.find(InternalFile,
                           InternalFile.file_path == unicode(file_path)).one()
    except Exception as err:
        log.err("Error in find %s: %s" % (file_path, err.message))
        return

    if not ifile:
        log.err("Unable to find %s" % file_path)
        return

    try:
        ifile.new = False
        ifile.file_path = new_path
    except Exception as excep:
        log.err("Unable to switch mode in InternalFile %s: %s" % (ifile.name, excep) )
        if new_path:
            log.err("+ filename switch fail: %s => %s" % (ifile.file_path, new_path))


def encrypt_where_available(receivermap):
    """
    @param receivermap:
        [ { 'receiver' : receiver_desc, 'path' : file_path, 'size' : file_size }, .. ]
    @return: return True if plaintex version of file must be created.
    """

    retcode = True

    for rcounter, rfileinfo in enumerate(receivermap):
        if rfileinfo['receiver']['pgp_key_status'] == u'enabled':
            try:
                new_path, new_size = fsops_pgp_encrypt(rfileinfo['path'], rfileinfo['receiver'])

                log.debug("%d# Switch on Receiver File for %s path %s => %s size %d => %d" % (
                    rcounter,  rfileinfo['receiver']['name'],
                    rfileinfo['path'], new_path, rfileinfo['size'], new_size )
                )

                # _status_list = [ u'reference', u'encrypted', u'unavailable' ]

                rfileinfo['path'] = new_path
                rfileinfo['size'] = new_size
                rfileinfo['status'] = u'encrypted'

            except Exception as excep:
                log.err("%d# Unable to complete PGP encrypt for %s on %s: %s. marking the file as unavailable." % (
                        rcounter, rfileinfo['receiver']['name'], rfileinfo['path'], excep)
                )
                rfileinfo['status'] = u'unavailable'
        elif GLSetting.memory_copy.allow_unencrypted:
            rfileinfo['status'] = u'reference'
            retcode = False
        else:
            rfileinfo['status'] = u'nokey'

    return retcode

class DeliverySchedule(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to process/validate files, compute their checksums and
        apply the configured delivery method.
        """
        filemap = yield receiverfile_planning()

        if not filemap:
            return

        # Here the files received are encrypted (if the receiver has PGP key)
        log.debug("Delivery task: Iterate over %d ReceiverFile(s)" % len(filemap.keys()))

        for ifile_path, receivermap in filemap.iteritems():
            plain_path = os.path.join(GLSetting.submission_path, "%s.plain" % xeger(r'[A-Za-z0-9]{16}') )

            create_plaintextfile = encrypt_where_available(receivermap)

            for rfileinfo in receivermap:
                if not create_plaintextfile and rfileinfo['status'] == u'reference':
                    rfileinfo['path'] = plain_path

                try:
                    yield receiverfile_create(ifile_path, rfileinfo['path'], rfileinfo['status'],
                                              rfileinfo['size'], rfileinfo['receiver'])

                except Exception as excep:
                    log.err("Unable to create ReceiverFile from %s for %s: %s" %
                            (ifile_path, rfileinfo['receiver']['name'], excep))
                    continue

            if not create_plaintextfile:
                log.debug(":( NOT all receivers support PGP and the system allows plaintext version of files: %s saved in plaintext file %s" %
                          (ifile_path, plain_path)
                )

                try:
                    with open(plain_path, "wb") as plain_f_is_sad_f, \
                         GLSecureFile(ifile_path) as encrypted_file:

                        chunk_size = 4096
                        while True:
                            chunk = encrypted_file.read(chunk_size)
                            if len(chunk) == 0:
                                break
                            plain_f_is_sad_f.write(chunk)

                    yield do_final_internalfile_update(ifile_path, plain_path)

                except Exception as excep:
                    log.err("Unable to create plaintext file %s: %s" % (plain_path, excep))

            else: # create_plaintextfile
                log.debug("All Receivers support PGP or the system denys plaintext version of files: marking internalfile as removed")
                yield do_final_internalfile_update(ifile_path, "")

            # the original AES file need always to be deleted
            log.debug("Deleting the submission AES encrypted file: %s" % ifile_path)
            try:
                os.remove(ifile_path)
            except OSError as ose:
                log.err("Unable to remove %s: %s" % (ifile_path, ose.message))

            try:
                key_id = os.path.basename(ifile_path).split('.')[0]
                keypath = os.path.join(GLSetting.ramdisk_path, ("%s%s" % (GLSetting.AES_keyfile_prefix, key_id)))
                os.remove(keypath)
            except Exception as excep:
                log.err("Unable to remove keyfile associated with %s: %s" % (ifile_path, excep))

            # here closes the if/else 'are_all_encrypted'
        # here closes the loop over internalfile mapping
    # here closes operations()

