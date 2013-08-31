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
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.utils import get_file_checksum, log, pretty_date_time
from globaleaks.security import GLBGPG
from globaleaks.handlers.admin import admin_serialize_receiver

__all__ = ['APSDelivery']

def serialize_internalfile(ifile):
    ifile_dict = {
        'id': ifile.id,
        'internaltip_id' : ifile.internaltip_id,
        'name' : ifile.name,
        'sha2sum' : ifile.sha2sum,
        'file_path' : ifile.file_path,
        'content_type' : ifile.content_type,
        'size' : ifile.size,
        'mark' : ifile.mark,
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
        'receiver_tip_id' : rfile.receiver_tip_id,
        'file_path' : rfile.file_path,
        'size' : rfile.size,
        'downloads' : rfile.downloads,
        'last_access' : rfile.last_access,
        'mark' : rfile.mark,
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

    REMIND: (keyword) esclation escalate pertinence vote
    here need to be updated whenever an escalation is implemented.
    checking of status and marker and recipients
    """

    try:
        files = store.find(InternalFile, InternalFile.mark == InternalFile._marker[0])
    except Exception as excep:
        log.err("Unable to find InternalFile in scheduler! %s" % str(excep))
        return []

    rfileslist = []
    for filex in files:

        if not filex.internaltip:
            log.err("Integrity failure: the file %s of %s"\
                    "has not an InternalTip assigned (path: %s)" %
                    (filex.name, pretty_date_time(filex.creation_date), filex.file_path) )

            try:
                store.remove(filex)
            except Exception as excep:
                log.err("Unable to remove InternalFile in scheduler! %s" % str(excep))
                continue

            try:
                os.unlink( os.path.join(GLSetting.submission_path, filex.file_path) )
            except OSError as excep:
                log.err("Unable to remove %s in integrity fixing routine: %s" %
                    (filex.file_path, excep.strerror) )
                continue

        # here we want to work on files with (Tip = 'finalize' or 'first' ) and (File = 'ready')
        # infact Tips may have two status both valid.
        # if these conditions are met the InternalFile(s) is/are marked as 'locked',
        # so that if a forced or planned delivery scheduler runs it doesn't touch the file already queued.
        if (filex.internaltip.mark == InternalTip._marker[1] or \
            filex.internaltip.mark == InternalTip._marker[2]) and \
            (filex.mark == InternalFile._marker[0]):
            filex.mark = InternalFile._marker[1] # 'locked'
        else:
            continue

        try:
            for receiver in filex.internaltip.receivers:
                receiver_desc = admin_serialize_receiver(receiver, GLSetting.memory_copy.default_language)

                if receiver_desc['gpg_key_status'] == Receiver._gpg_types[1] and receiver_desc['gpg_enable_files']:
                    rfileslist.append([ filex.id,
                                        ReceiverFile._status_list[2], # encrypted
                                        filex.file_path, receiver_desc ])
                else:
                    rfileslist.append([ filex.id,
                                        ReceiverFile._status_list[1], # reference
                                        filex.file_path, receiver_desc ])
        except Exception as excep:
            log.debug("Invalid Storm operation in checking for GPG cap: %s" % excep)
            continue

    return rfileslist


# It's not a transact because works on FS
def fsops_compute_checksum(rfilelist):
    """
    @param rfilelist:
        $id
        $status
        $path
        $receiver description dict
    @return:
    """

    assert isinstance(rfilelist, list)
    assert len(rfilelist) >= 1

    # extract only the single file_id : file_path
    filesdict = {}
    for rfileblob in rfilelist:

        if filesdict.has_key(rfileblob[0]):
            assert filesdict[rfileblob[0]] == rfileblob[2], "Invalid path/id"

        filesdict.update({rfileblob[0]:rfileblob[2]})

    # loop and compute checksum
    processdict = {}
    for file_id, file_path in filesdict.iteritems():

        file_location = os.path.join(GLSetting.submission_path, file_path)
        checksum, orig_len = get_file_checksum(file_location)
        processdict.update({file_id : { 'checksum': checksum,
                                        'olen': orig_len }
        })

    return processdict

def fsops_gpg_encrypt(fpath, recipient_gpg):
    """
    return
        path of encrypted file,
        length of the encrypted file

    this function is used to encrypt a file for a specific recipient.
    commonly 'receiver_desc' is expected as second argument;
    anyhow a simpler dict can be used.

    required keys are checked on top

    """
    assert isinstance(recipient_gpg, dict), "invalid recipient"
    assert recipient_gpg.has_key('gpg_key_armor'), "missing key"
    assert recipient_gpg.has_key('gpg_key_status'), "missing status"
    assert recipient_gpg['gpg_key_status'] == u'Enabled', "GPG not enabled"
    assert recipient_gpg.has_key('name'), "missing recipient Name"

    try:
        gpoj = GLBGPG(recipient_gpg)

        if not gpoj.validate_key(recipient_gpg['gpg_key_armor']):
            raise Exception("Unable to validate key")

        ifile_abs = os.path.join(GLSetting.submission_path, fpath)

        with file(ifile_abs, "r") as f:
            encrypted_file_path, encrypted_file_size = \
                gpoj.encrypt_file(ifile_abs, f, GLSetting.submission_path)

        gpoj.destroy_environment()

        assert encrypted_file_size > 1
        assert os.path.isfile(encrypted_file_path)

        return encrypted_file_path, encrypted_file_size

    except Exception as excep:
        # Yea, please, don't mention protocol downgrade.
        log.err("Error in encrypting %s for %s: fallback in plaintext (%s)" % (
            fpath, recipient_gpg['name'], excep
        ) )
        raise excep


@transact
def receiverfile_create(store, fid, status, fpath, flen, cksum, receiver_desc):

    assert type(1) == type(flen)
    assert isinstance(status, unicode) and isinstance(cksum, str)
    assert isinstance(receiver_desc, dict)
    assert os.path.isfile(os.path.join(GLSetting.submission_path, fpath))

    try:
        ifile = store.find(InternalFile, InternalFile.id == unicode(fid)).one()

        # update the internalfile with the computed sha
        if not ifile.sha2sum:
            ifile.sha2sum = unicode(cksum)
        else:
            assert ifile.sha2sum == cksum, "checksum fail!"

        log.debug("ReceiverFile creation for user %s, file %s (%d %s)"
                % (receiver_desc['name'], ifile.name, flen, status ) )
        receiverfile = ReceiverFile()

        receiverfile.downloads = 0
        receiverfile.receiver_id = receiver_desc['receiver_gus']
        receiverfile.internalfile_id = ifile.id
        receiverfile.internaltip_id = ifile.internaltip_id

        # Receiver Tip reference
        rtrf = store.find(ReceiverTip, ReceiverTip.internaltip_id == ifile.internaltip_id,
                          ReceiverTip.receiver_id == receiver_desc['receiver_gus']).one()
        receiverfile.receiver_tip_id = rtrf.id

        # inherit by previous operation and checks
        receiverfile.file_path = fpath
        receiverfile.size = flen
        receiverfile.status = status

        receiverfile.mark = ReceiverFile._marker[0] # not notified

        store.add(receiverfile)
        store.commit()

        # to avoid eventual file leakage or inconsistency, now is
        # loaded the object to verify reference

        test = store.find(ReceiverFile, ReceiverFile.internalfile_id == fid,
                          ReceiverFile.receiver_id == receiver_desc['receiver_gus']).one()

        # assert over context, filesystem and receiver state
        assert test.internaltip.context_id, "Context broken"
        assert os.path.isfile(
            os.path.join(GLSetting.submission_path,
                         test.file_path)), "FS broken (r)"
        assert os.path.isfile(
            os.path.join(GLSetting.submission_path,
                         test.internalfile.file_path)), "FS broken (i)"
        assert test.receiver.user.state != u'disabled', "User broken"

        return serialize_receiverfile(receiverfile)

    except Exception as excep:
        log.err("Error when saving ReceiverFile %s for %s: %s" % (
                fpath, receiver_desc['name'], str(excep) ))
        return []


# called in a transact!
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

    if len(created_rtip):
        log.debug("The finalized submissions had created %d ReceiverTip(s)" % len(created_rtip))

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


@transact
def do_final_internalfile_update(store, ifile_track):

    assert isinstance(ifile_track, dict), "ifile_track is wrong"
    for file_id, status in ifile_track.iteritems():
        ifil = store.find(InternalFile, InternalFile.id == unicode(file_id)).one()

        try:
            ifil.mark = status
            store.commit()
        except Exception as excep:
            log.err("Unable to commit final mod in InternalFile: %s" % excep)
            continue

        log.debug("Status sets for ifile %s = %s" %(
            file_id, status
        ))



class APSDelivery(GLJob):

    @inlineCallbacks
    def operation(self):
        """
        Goal of this function is to process/validate files, compute their checksums and
        apply the configured delivery method.
        """

        try:
            # ==> Submission && Escalation
            info_created_tips = yield tip_creation()
            if info_created_tips:
                log.debug("Delivery job: created %d tips" % len(info_created_tips))
        except Exception as excep:
            log.err("Exception in asyncronous delivery job: %s" % excep )
            sys.excepthook(*sys.exc_info())

        # ==> Files && Files update,
        #     InternalFile set as 'locked' status
        #
        # all exceptions handled inside.
        #     
        # the function returns a list of lists:
        #     [ "file_id", status, "f_path", len, "receiver_desc" ]
        rfileslist = yield receiverfile_planning()

        if not rfileslist:
            return

        # computes checksum and  processes the file on the disk here,
        # outside of the SQL transaction.
        #
        # all exceptions handled inside.
        #
        # the function returns a dict 
        #     { "file_uuid" : [ file_len, checksum ] }
        checksums = fsops_compute_checksum(rfileslist)

        log.debug("Delivery task: received %d new file, generating %d receiver file" % (
            len(checksums), len(rfileslist)))

        for (fid, status, fpath, receiver_desc) in rfileslist:

            # this is the plain text length (and checksum)
            flen = checksums[fid]['olen']

            if status == ReceiverFile._status_list[2]: # 'encrypted'
                try:
                    fpath, flen = fsops_gpg_encrypt(fpath, receiver_desc)
                except Exception as excep:
                    log.err("Unable to complete GPG encrypt on %s for %s: %s" %
                            (fpath, receiver_desc['name'], excep))
                    continue

            try:
                yield receiverfile_create(fid, status, fpath, flen, checksums[fid]['checksum'], receiver_desc)
            except Exception as excep:
                log.err("Unable to create receiverfile from %s for %s: %s" %
                        (fpath, receiver_desc['name'], excep))
                continue

        # This loop permits to remove internalfile that is no more useful after the creation of receivertip.
        # e.g.: all the receiver have GPG key and so the reference is useless.
        ifile_track = {}
        for ifile_id, check in checksums.iteritems():
            almost_one_reference = False

            for (fid, status, fname, receiver_desc) in rfileslist:
                if ifile_id == fid and status == 'reference':
                    almost_one_reference = True

            if not almost_one_reference:
                log.debug("Removing useless plain file: %s" % fname)
                path = os.path.join(GLSetting.submission_path, fname)
                try:
                    os.unlink(path)
                except Exception as excep:
                    log.err("Unable to remove ifile in %s: %s" % (
                        path, str(excep)
                    ))
                    # In DB remain registered the  status 'locked'; may arise suspects anyway
                    continue

                ifile_track.update({fid: InternalFile._marker[3] }) # Removed
            else:
                ifile_track.update({fid: InternalFile._marker[2] }) # Ready

        yield do_final_internalfile_update(ifile_track)
        # completed in love! http://www.youtube.com/watch?v=CqLAwt8T3Ps

