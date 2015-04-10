# -*- coding: utf-8 -*-
#
# files
#  *****
#
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement
import shutil

import os
from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated, unauthenticated
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now
from globaleaks.rest import errors
from globaleaks.models import ReceiverFile, InternalTip, InternalFile, WhistleblowerTip
from globaleaks.security import access_tip
from globaleaks.utils.token import TokenList


def serialize_file(internalfile):
    file_desc = {
        'size': internalfile.size,
        'content_type': internalfile.content_type,
        'name': internalfile.name,
        'creation_date': datetime_to_ISO8601(internalfile.creation_date),
        'id': internalfile.id
    }

    return file_desc


def serialize_receiver_file(receiverfile):
    internalfile = receiverfile.internalfile

    file_desc = {
        'size': receiverfile.size,
        'content_type': internalfile.content_type,
        'name': ("%s.pgp" % internalfile.name) if receiverfile.status == u'encrypted' else internalfile.name,
        'creation_date': datetime_to_ISO8601(internalfile.creation_date),
        'downloads': receiverfile.downloads,
        'path': receiverfile.file_path,
    }

    return file_desc


def serialize_memory_file(uploaded_file):
    """
    This is the memory version of the function register_file_db below,
    return the file serialization used by JQueryFileUploader to display
    information about our file.
    """
    return {
        'content_type': unicode(uploaded_file['content_type']),
        'creation_date': datetime_to_ISO8601(uploaded_file['creation_date']),
        'id': u'00000000-0000-0000-0000-000000000000',
        # 'id' is ignored, TODO align API/requsts.py
        'name': unicode(uploaded_file['filename']),
        'size': uploaded_file['body_len'],
    }


@transact
def register_file_db(store, uploaded_file, internaltip_id):
    """
    Remind: this is used only with fileApp - Tip append a new file,
    for the submission section, we relay on Token to keep track of the
    associated file, and in handlers/submission.py InternalFile(s) are
    created.

    :param uploaded_file: contain this struct of data:
        {
          'body': <closed file u'/home/qq/Dev/GlobaLeaks/backend/workingdir/files/encrypted_upload/lryZO8IlldGg3BS3.aes', mode 'w+b' at 0xb5b68498>,
          'body_len': 667237,
          'content_type': 'image/png',
          'encrypted_path': u'/home/XYZ/Dev/GlobaLeaks/backend/workingdir/files/submission/lryZO8IlldGg3BS3.aes',
          'filename': 'SteganographyIsImportant.png'
        }
    """
    internaltip = store.find(InternalTip,
                             InternalTip.id == internaltip_id).one()

    if not internaltip:
        log.err("File associated to a non existent Internaltip!")
        raise errors.TipIdNotFound

    new_file = InternalFile()
    new_file.name = uploaded_file['filename']
    new_file.content_type = uploaded_file['content_type']
    new_file.size = uploaded_file['body_len']
    new_file.internaltip_id = internaltip_id
    new_file.file_path = uploaded_file['encrypted_path']
    new_file.is_e2e_encrypted = GLSetting.memory_copy.file_encryption_e2e

    if GLSetting.memory_copy.file_encryption_e2e:
        log.debug("End2End enabled node level - File")
    else:
        log.debug("End2End DIS-abled node level - File")

    store.add(new_file)

    log.debug("=> Recorded new InternalFile %s" % uploaded_file['filename'])

    return serialize_file(new_file)


def dump_file_fs(uploaded_file):
    """
    @param files: the JQFU dict with file infos
    @return: the uploaded_file dict, removed the old path (is moved) and updated
            with the key 'encrypted_path', pointing to the AES encrypted file
    """
    encrypted_destination = os.path.join(GLSetting.submission_path,
                                         os.path.basename(uploaded_file['body_filepath']))

    log.debug("Moving encrypted bytes %d from file [%s] %s => %s" %
              (uploaded_file['body_len'],
               uploaded_file['filename'],
               uploaded_file['body_filepath'],
               encrypted_destination)
              )

    shutil.move(uploaded_file['body_filepath'], encrypted_destination)

    # body_filepath is the tmp file path, is removed to avoid mistakes
    uploaded_file.pop('body_filepath')

    # update the uploaded_file dictionary to keep track of the info
    uploaded_file['encrypted_path'] = encrypted_destination
    return uploaded_file


@transact_ro
def get_itip_id_by_wbtip_id(store, wb_tip_id):
    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == wb_tip_id).one()

    if not wb_tip:
        raise errors.InvalidAuthentication

    return wb_tip.internaltip.id


# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(BaseHandler):
    """
    WhistleBlower interface for upload a new file in an already completed submission
    """

    @inlineCallbacks
    def handle_file_append(self, itip_id):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        uploaded_file['body'].avoid_delete()
        uploaded_file['body'].close()

        try:
            # First: dump the file in the filesystem,
            # and exception raised here would prevent the InternalFile recordings
            uploaded_file = yield threads.deferToThread(dump_file_fs, uploaded_file)
        except Exception as excep:
            log.err("Unable to save a file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")
        try:
            # Second: register the file in the database
            registered_file = yield register_file_db(uploaded_file, itip_id)
        except Exception as excep:
            log.err("Unable to register (append) file in DB: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")

    @transport_security_check('wb')
    @unauthenticated
    def get(self, *args):
        """
        Parameter: internaltip_id
        Request: Unknown
        Response: Unknown
        Errors: TokenFailure
        """
        self.set_status(204)  # We currently do not implement file resume
        self.finish()

    @transport_security_check('wb')
    @authenticated('wb')
    @inlineCallbacks
    def post(self, *args):
        """
        Request: Unknown
        Response: Unknown
        Errors: TipIdNotFound

        This is not manage by token, is unchanged by the D8 update,
        because is an operation tip-established, and they can be
        rate-limited in a different way.
        """
        itip_id = yield get_itip_id_by_wbtip_id(self.current_user.user_id)

        yield self.handle_file_append(itip_id)

        self.set_status(201)  # Created
        self.finish()


class FileInstance(BaseHandler):
    """
    WhistleBlower interface for upload a new file in a not yet completed submission
    """

    @inlineCallbacks
    def handle_file_upload(self, token):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        uploaded_file['body'].avoid_delete()
        uploaded_file['body'].close()

        try:
            # dump_file_fs return the new filepath inside the dictionary
            uploaded_file = yield threads.deferToThread(dump_file_fs, uploaded_file)
            uploaded_file['creation_date'] = datetime_now()

            token.associate_file(uploaded_file)

            registered_file = serialize_memory_file(uploaded_file)
        except Exception as excep:
            log.err("Unable to save file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept files")

    @transport_security_check('wb')
    @unauthenticated
    def get(self, token_id):
        """
        Parameter: internaltip_id
        Request: Unknown
        Response: Unknown
        Errors: TokenFailure
        """
        token = TokenList.get(token_id)

        self.set_status(204)  # We currently do not implement file resume
        self.finish()

    @transport_security_check('wb')
    @unauthenticated
    @inlineCallbacks
    def post(self, token_id):
        """
        Parameter: internaltip_id
        Request: Unknown
        Response: Unknown
        Errors: TokenFailure
        """
        token = TokenList.get(token_id)

        log.debug("file upload with token associated: %s" % token)

        yield self.handle_file_upload(token)

        self.set_status(201)  # Created
        self.finish()


@transact
def download_file(store, user_id, tip_id, file_id):
    """
    Auth temporary disabled, just Tip_id and File_id required
    """
    access_tip(store, user_id, tip_id)

    rfile = store.find(ReceiverFile,
                       ReceiverFile.id == unicode(file_id)).one()

    if not rfile or rfile.receiver_id != user_id:
        raise errors.FileIdNotFound

    log.debug("Download of file %s by receiver %s (%d)" %
              (rfile.internalfile.id, rfile.receiver.id, rfile.downloads))

    rfile.downloads += 1

    return serialize_receiver_file(rfile)


@transact
def download_all_files(store, user_id, tip_id):
    access_tip(store, user_id, tip_id)

    rfiles = store.find(ReceiverFile,
                        ReceiverFile.receivertip_id == unicode(tip_id))

    files_list = []
    for sf in rfiles:
        sf.downloads += 1
        files_list.append(serialize_receiver_file(sf))

    return files_list


class Download(BaseHandler):
    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id, rfile_id):
        rfile = yield download_file(self.current_user.user_id, tip_id, rfile_id)

        # keys:  'file_path'  'size' : 'content_type' 'file_name'

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Length', rfile['size'])
        self.set_header('Content-Disposition', 'attachment; filename=\"%s\"' % rfile['name'])

        filelocation = os.path.join(GLSetting.submission_path, rfile['path'])

        self.write_file(filelocation)

        self.finish()
