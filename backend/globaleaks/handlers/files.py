# -*- coding: utf-8 -*-
#
# files
#  *****
#
# API handling submissions file uploads and subsequent submissions attachments
import shutil

import os

from cyclone.web import asynchronous
from storm.expr import And
from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_get_rtip
from globaleaks.handlers.submission import serialize_receiver_tip, \
    serialize_internalfile, serialize_receiverfile
from globaleaks.models import ReceiverFile, InternalTip, InternalFile
from globaleaks.rest import errors
from globaleaks.security import GLSecureFile
from globaleaks.settings import GLSettings
from globaleaks.utils.token import TokenList
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now


def serialize_memory_file(uploaded_file):
    """
    This is the memory version of the function register_file_db below,
    return the file serialization used by JQueryFileUploader to display
    information about our file.
    """
    return {
        'content_type': unicode(uploaded_file['content_type']),
        'creation_date': datetime_to_ISO8601(uploaded_file['creation_date']),
        'name': unicode(uploaded_file['filename']),
        'size': uploaded_file['body_len'],
    }


@transact
def register_file_db(store, uploaded_file, internaltip_id):
    internaltip = store.find(InternalTip,
                             InternalTip.id == internaltip_id).one()

    if not internaltip:
        log.err("File associated to a non existent Internaltip!")
        raise errors.TipIdNotFound

    internaltip.update_date = datetime_now()

    ifile = InternalFile()
    ifile.name = uploaded_file['filename']
    ifile.content_type = uploaded_file['content_type']
    ifile.size = uploaded_file['body_len']
    ifile.internaltip_id = internaltip_id
    ifile.submission = uploaded_file['submission']
    ifile.file_path = uploaded_file['body_filepath']

    store.add(ifile)

    log.debug("InternalFile registered on the db")

    return serialize_internalfile(ifile)


def dump_file_fs(uploaded_file):
    """
    @param uploaded_file: the uploaded_file data struct
    @return: the uploaded_file dict updated with the final path of the ifile
    """
    destination = os.path.join(GLSettings.submission_path,
                               os.path.basename(uploaded_file['body_filepath']))

    shutil.move(uploaded_file['body_filepath'], destination)

    uploaded_file['body_filepath'] = destination

    return uploaded_file


# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(BaseHandler):
    """
    WhistleBlower interface for upload a new file in an already completed submission
    """
    handler_exec_time_threshold = 3600
    filehandler = True

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

        uploaded_file['creation_date'] = datetime_now()
        uploaded_file['submission'] = False

        try:
            # Second: register the file in the database
            yield register_file_db(uploaded_file, itip_id)
        except Exception as excep:
            log.err("Unable to register (append) file in DB: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")

    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
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
        yield self.handle_file_append(self.current_user.user_id)

        self.set_status(201)  # Created


class FileInstance(BaseHandler):
    """
    WhistleBlower interface for upload a new file in a not yet completed submission
    """
    handler_exec_time_threshold = 3600
    filehandler = True

    @inlineCallbacks
    def handle_file_upload(self, token_id):
        token = TokenList.get(token_id)

        log.debug("file upload with token associated: %s" % token)

        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        uploaded_file['body'].avoid_delete()
        uploaded_file['body'].close()

        try:
            # dump_file_fs return the new filepath inside the dictionary
            uploaded_file = yield threads.deferToThread(dump_file_fs, uploaded_file)
            uploaded_file['creation_date'] = datetime_now()
            uploaded_file['submission'] = True

            token.associate_file(uploaded_file)

            serialize_memory_file(uploaded_file)
        except Exception as excep:
            log.err("Unable to save file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept files")

    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.unauthenticated
    @inlineCallbacks
    def post(self, token_id):
        """
        Parameter: internaltip_id
        Request: Unknown
        Response: Unknown
        Errors: TokenFailure
        """
        yield self.handle_file_upload(token_id)

        self.set_status(201)  # Created


@transact
def download_file(store, user_id, rtip_id, file_id):
    rtip = db_get_rtip(store, user_id, rtip_id)

    rfile = store.find(ReceiverFile,
                       And(ReceiverFile.id == file_id,
                           ReceiverFile.receivertip_id == rtip_id)).one()

    if not rfile:
        raise errors.FileIdNotFound

    log.debug("Download of file %s by receiver %s (%d)" %
              (rfile.internalfile_id, rfile.receiver_id, rfile.downloads))

    rfile.downloads += 1

    return serialize_receiverfile(rfile)


class Download(BaseHandler):
    handler_exec_time_threshold = 3600

    @BaseHandler.transport_security_check('receiver')
    @BaseHandler.authenticated('receiver')
    @asynchronous
    @inlineCallbacks
    def get(self, rtip_id, rfile_id):
        rfile = yield download_file(self.current_user.user_id, rtip_id, rfile_id)

        filelocation = os.path.join(GLSettings.submission_path, rfile['file_path'])

        if os.path.exists(filelocation):
            self.set_header('X-Download-Options', 'noopen')
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Length', rfile['size'])
            self.set_header('Content-Disposition', 'attachment; filename=\"%s\"' % rfile['name'])
            self.write_file(filelocation)
        else:
            self.set_status(404)
