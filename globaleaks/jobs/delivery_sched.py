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
from globaleaks.utils.utility import log, pretty_date_time
from globaleaks.security import GLBGPG, GLSecureFile
from globaleaks.handlers.admin import admin_serialize_receiver
from globaleaks.third_party.rstr import xeger

__all__ = ['DeliverySchedule']

def serialize_internalfile(ifile):
    ifile_dict = {
        'id': ifile.id,
        'internaltip_id' : ifile.internaltip_id,
        'name' : ifile.name,
        'description' : ifile.description,
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

    REMIND: (keyword) escalation escalate pertinence vote
    here need to be updated whenever an escalation is implemented.
    checking of status and marker and recipients
    """

    try:
        files = store.find(InternalFile, InternalFile.mark == InternalFile._marker[0])
    except Exception as excep:
        log.err("Unable to find InternalFile in scheduler! %s" % str(excep))
        return []

    ifilesmap = {}

    for filex in files:

        if not filex.internaltip:
            log.err("Integrity failure: the file %s of %s"\
                    "has not an InternalTip assigned (path: %s)" %
                    (filex.name, pretty_date_time(filex.creation_date), filex.file_path) )

            try:
                os.remove(os.path.join(GLSetting.submission_path, filex.file_path))
            except OSError as excep:
                log.err("Unable to remove %s in integrity fixing routine: %s" %
                    (filex.file_path, excep.strerror) )

            try:
                key_id = os.path.basename(filex.file_path).split('.')[0]
                keypath = os.path.join(GLSetting.ramdisk_path, ("%s%s" % (GLSetting.AES_keyfile_prefix, key_id)))
                os.remove(keypath)
            except Exception as excep:
                log.err("Unable to keyfile %s in integrity fixing routine: %s" % (keypath, excep))

            continue

        # here we select the file which deserve to be processed.
        # They need to be:
        #   From a Tip in (Tip = 'finalize' or 'first' )
        #   From an InternalFile (File = 'ready')
        # Tips may have two statuses both valid.
        # if these conditions are met the InternalFile(s) is/are marked as 'locked',
        # Whenever a delivery scheduler run, do not touch 'locked' file, and if 'locked' file
        # appears in the Admin interface of file overview, this mean that something is broken.
        if (filex.internaltip.mark == InternalTip._marker[1] or \
            filex.internaltip.mark == InternalTip._marker[2]) and \
            (filex.mark == InternalFile._marker[0]):
            filex.mark = InternalFile._marker[1] # 'locked'
        else:
            continue

        try:

            for receiver in filex.internaltip.receivers:

                if not ifilesmap.has_key(filex.file_path):
                    ifilesmap[filex.file_path] = list()

                receiver_desc = admin_serialize_receiver(receiver, GLSetting.memory_copy.default_language)

                map_info = {
                    'receiver' : receiver_desc,
                    'path' : filex.file_path,
                    'size' : filex.size,
                    'status' : ReceiverFile._status_list[1] # reference
                }

                # this may seem apparently redounded, but is not!
                # AS KEY, file path is used to keep track of the original
                # path, because shall be renamed in .plaintext (in the unlucky case
                # of receivers without PGP)
                # AS FIELD, it can be replaced with a dedicated PGP encrypted path
                ifilesmap[filex.file_path].append(map_info)

        except Exception as excep:
            log.debug("Invalid Storm operation in checking for PGP cap: %s" % excep)
            continue

    return ifilesmap


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

    gpoj = GLBGPG(recipient_gpg)

    if not gpoj.validate_key(recipient_gpg['gpg_key_armor']):
        raise Exception("Unable to validate key")

    filepath = os.path.join(GLSetting.submission_path, fpath)

    with GLSecureFile(filepath) as f:
        encrypted_file_path, encrypted_file_size = \
            gpoj.encrypt_file(filepath, f, GLSetting.submission_path)

    gpoj.destroy_environment()

    assert (encrypted_file_size > 1), "File generated is empty or size is 0"
    assert os.path.isfile(encrypted_file_path), "Output generated is not a file!"

    return encrypted_file_path, encrypted_file_size

@transact
def receiverfile_create(store, if_path, recv_path, status, recv_size, receiver_desc):

    assert type(1) == type(recv_size)
    assert isinstance(receiver_desc, dict)
    assert os.path.isfile(os.path.join(GLSetting.submission_path, if_path))

    try:
        ifile = store.find(InternalFile, InternalFile.file_path == unicode(if_path)).one()

        if not ifile:
            log.err("InternalFile with path %s not found !?" % if_path)
            raise Exception("This is bad!")

        log.debug("ReceiverFile creation for user %s, '%s' bytes %d = %s)"
                % (receiver_desc['name'], ifile.name, recv_size, status ) )

        receiverfile = ReceiverFile()

        receiverfile.downloads = 0
        receiverfile.receiver_id = receiver_desc['id']
        receiverfile.internalfile_id = ifile.id
        receiverfile.internaltip_id = ifile.internaltip_id

        # Receiver Tip reference
        rtrf = store.find(ReceiverTip, ReceiverTip.internaltip_id == ifile.internaltip_id,
                          ReceiverTip.receiver_id == receiver_desc['id']).one()
        receiverfile.receiver_tip_id = rtrf.id

        # inherited by previous operation and checks
        receiverfile.file_path = unicode(recv_path)
        receiverfile.size = recv_size
        receiverfile.status = unicode(status)

        receiverfile.mark = ReceiverFile._marker[0] # not notified

        store.add(receiverfile)

        return serialize_receiverfile(receiverfile)

    except Exception as excep:
        log.err("Error when saving ReceiverFile %s for '%s': %s" % (
                if_path, receiver_desc['name'], excep.message))
        return []


# called in a transact!
def create_receivertip(store, receiver, internaltip, tier):
    """
    Create ReceiverTip for the required tier of Receiver.
    """
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
def do_final_internalfile_update(store, file_path, new_marker, new_path=None):

    try:
        ifile = store.find(InternalFile,
                           InternalFile.file_path == unicode(file_path)).one()
    except Exception as stormer:
        log.err("Error in find %s: %s" % (file_path, stormer.message))
        return

    if not ifile:
        log.err("Unable to find %s" % file_path)
        return

    try:
        old_marker = ifile.mark
        ifile.mark = new_marker

        if new_path:
            ifile.file_path = new_path

        log.debug("Switched status set for InternalFile %s (%s => %s)" %(
            ifile.name, old_marker, new_marker
        ))

    except Exception as excep:
        log.err("Unable to switch mode in InternalFile %s: %s" % (ifile.name, excep) )
        if new_path:
            log.err("+ filename switch fail: %s => %s" % (ifile.file_path, new_path))


def encrypt_where_available(receivermap):
    """
    @param receivermap:
        [ { 'receiver' : receiver_desc, 'path' : file_path, 'size' : file_size }, .. ]
    @return: return True if all the receiver permit GPG encryption
    """

    retcode = True

    for rcounter, rfileinfo in enumerate(receivermap):

        if rfileinfo['receiver']['gpg_key_status'] == Receiver._gpg_types[1]:

            try:
                new_path, new_size = fsops_gpg_encrypt(rfileinfo['path'], rfileinfo['receiver'])

                log.debug("%d# Switch on Receiver File for %s path %s => %s size %d => %d" % (
                    rcounter,  rfileinfo['receiver']['name'],
                    rfileinfo['path'], new_path, rfileinfo['size'], new_size )
                )

                # _status_list = [ u'cloned', u'reference', u'encrypted', u'unavailable' ]

                rfileinfo['path'] = new_path
                rfileinfo['size'] = new_size
                rfileinfo['status'] = ReceiverFile._status_list[2] # encrypted

            except Exception as excep:
                log.err("%d# Unable to complete GPG encrypt for %s on %s: %s. marking the file as unavailable." % (
                        rcounter, rfileinfo['receiver']['name'], rfileinfo['path'], excep)
                )
                rfileinfo['status'] = ReceiverFile._status_list[3] # unavailable
                continue
        else:
            rfileinfo['status'] = ReceiverFile._status_list[1] # reference
            retcode = False

    return retcode

class DeliverySchedule(GLJob):

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
        #     InternalFile is set as 'locked' status
        #     and would be unlocked at the end.
        # TODO xxx limit of file number per operation
        filemap = yield receiverfile_planning()
        # the function returns a dict of lists with dicts:
        # {
        #     'ifile_path' : [
        #       { 'receiver' : receiver_desc, 'path': file_path,
        #                           'size' : file_size, 'status': XXX },
        #       { 'receiver' : receiver_desc, 'path': file_path,
        #                           'size' : file_size, 'status': YYY }, ... ]
        # },  { }, ...
        #

        if not filemap:
            return

        # Here the files received are encrypted (if the receiver has PGP key)
        log.debug("Delivery task: Iterate over %d ReceiverFile(s)" % len(filemap.keys()) )

        for ifile_path, receivermap in filemap.iteritems():

            plain_path = os.path.join(GLSetting.submission_path, "%s.plain" % xeger(r'[A-Za-z0-9]{16}') )

            are_all_encrypted = encrypt_where_available(receivermap)

            for rfileinfo in receivermap:

                if not are_all_encrypted and rfileinfo['status'] == u'reference':
                    rfileinfo['path'] = plain_path

                try:
                    yield receiverfile_create(ifile_path, rfileinfo['path'], rfileinfo['status'],
                                              rfileinfo['size'], rfileinfo['receiver'])
                except Exception as excep:
                    log.err("Unable to create ReceiverFile from %s for %s: %s" %
                            (ifile_path, rfileinfo['receiver']['name'], excep))
                    continue

            if not are_all_encrypted:
                log.debug(":( NOT all receivers support PGP %s go to unsafe version %s" %
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

                    yield do_final_internalfile_update(ifile_path, InternalFile._marker[2], plain_path)

                except Exception as excep:
                    log.err("Unable to create plaintext file %s: %s" % plain_path, excep)

            else: # are_all_encrypted:
                log.debug("All Receivers support PGP, marking internalfile as removed")
                yield do_final_internalfile_update(ifile_path, InternalFile._marker[3]) # Removed

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

