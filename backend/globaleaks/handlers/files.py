# -*- coding: utf-8 -*-
#
# files
#  *****
#
# API handling submissions file uploads and subsequent submissions attachments
import os
import shutil

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler, write_upload_encrypted_to_disk
from globaleaks.models import ReceiverFile, InternalTip, InternalFile, WhistleblowerTip
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.security import directory_traversal_check
from globaleaks.settings import GLSettings
from globaleaks.utils.token import TokenList
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now


def serialize_ifile(ifile):
    return {
        'id': ifile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ifile.name,
        'size': ifile.size,
        'content_type': ifile.content_type
    }


def serialize_rfile(rfile):
    ifile = rfile.internalfile

    return {
        'id': rfile.id,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
        'name': ("%s.pgp" % ifile.name) if rfile.status == u'encrypted' else ifile.name,
        'content_type': ifile.content_type,
        'size': rfile.size,
        'path': rfile.file_path,
        'downloads': rfile.downloads
    }


@transact
def register_ifile_on_db(store, uploaded_file, internaltip_id):
    internaltip = store.find(InternalTip,
                             InternalTip.id == internaltip_id).one()

    if not internaltip:
        log.err("File associated to a non existent Internaltip!")
        raise errors.TipIdNotFound

    internaltip.update_date = datetime_now()

    new_file = InternalFile()
    new_file.name = uploaded_file['name']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.internaltip_id = internaltip_id
    new_file.submission = uploaded_file['submission']
    new_file.file_path = uploaded_file['path']

    store.add(new_file)

    log.debug("=> Recorded new InternalFile %s" % uploaded_file['name'])

    return serialize_ifile(new_file)


@transact
def get_itip_id_by_wbtip_id(store, wbtip_id):
    wbtip = store.find(WhistleblowerTip,
                       WhistleblowerTip.id == wbtip_id).one()

    if not wbtip:
        raise errors.InvalidAuthentication

    return wbtip.internaltip_id


# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(BaseHandler):
    """
    WhistleBlower interface for upload a new file in an already completed submission
    """
    handler_exec_time_threshold = 3600
    filehandler = True

    @BaseHandler.transport_security_check('whistleblower')
    @BaseHandler.authenticated('whistleblower')
    @inlineCallbacks
    def post(self):
        """
        Request: Unknown
        Response: Unknown
        Errors: TipIdNotFound
        """
        itip_id = yield get_itip_id_by_wbtip_id(self.current_user.user_id)

        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        uploaded_file['body'].avoid_delete()
        uploaded_file['body'].close()

        try:
            # First: dump the file in the filesystem
            dst = os.path.join(GLSettings.submission_path,
                               os.path.basename(uploaded_file['path']))

            directory_traversal_check(GLSettings.submission_path, dst)

            uploaded_file = yield threads.deferToThread(write_upload_encrypted_to_disk, uploaded_file, dst)
        except Exception as excep:
            log.err("Unable to save a file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")

        uploaded_file['date'] = datetime_now()
        uploaded_file['submission'] = False

        try:
            # Second: register the file in the database
            yield register_ifile_on_db(uploaded_file, itip_id)
        except Exception as excep:
            log.err("Unable to register (append) file in DB: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")

        self.set_status(201)  # Created


class FileInstance(BaseHandler):
    """
    WhistleBlower interface for upload a new file in a not yet completed submission
    """
    handler_exec_time_threshold = 3600
    filehandler = True

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
        token = TokenList.get(token_id)

        log.debug("file upload with token associated: %s" % token)

        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        uploaded_file['body'].avoid_delete()
        uploaded_file['body'].close()

        try:
            dst = os.path.join(GLSettings.submission_path,
                               os.path.basename(uploaded_file['path']))

            directory_traversal_check(GLSettings.submission_path, dst)

            uploaded_file = yield threads.deferToThread(write_upload_encrypted_to_disk, uploaded_file, dst)
            uploaded_file['date'] = datetime_now()
            uploaded_file['submission'] = True

            token.associate_file(uploaded_file)
        except Exception as excep:
            log.err("Unable to save file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept files")

        self.set_status(201)  # Created
