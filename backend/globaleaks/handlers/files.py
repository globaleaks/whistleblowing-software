# -*- coding: utf-8 -*-
#
# files
#  *****
#
# API handling submissions file uploads and subsequent submissions attachments
import os

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler, write_upload_encrypted_to_disk
from globaleaks.models import serializers
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.security import directory_traversal_check
from globaleaks.settings import GLSettings
from globaleaks.utils.token import TokenList
from globaleaks.utils.utility import log, datetime_now


@transact
def register_ifile_on_db(store, uploaded_file, internaltip_id):
    internaltip = models.db_get(store, models.InternalTip, id=internaltip_id)

    internaltip.update_date = datetime_now()

    new_file = models.InternalFile()
    new_file.name = uploaded_file['name']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.internaltip_id = internaltip_id
    new_file.submission = uploaded_file['submission']
    new_file.file_path = uploaded_file['path']
    store.add(new_file)

    return serializers.serialize_ifile(store, new_file)


@transact
def get_itip_id_by_wbtip_id(store, wbtip_id):
    wbtip = store.find(models.WhistleblowerTip, id=wbtip_id).one()

    if not wbtip:
        raise errors.InvalidAuthentication

    return wbtip.id


# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(BaseHandler):
    """
    WhistleBlower interface to upload a new file for an already completed submission
    """
    check_roles = 'whistleblower'
    handler_exec_time_threshold = 3600

    @inlineCallbacks
    def post(self):
        """
        Request: Unknown
        Response: Unknown
        Errors: ModelNotFound
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
            print excep
            raise errors.InternalServerError("Unable to accept new files")

        uploaded_file['date'] = datetime_now()
        uploaded_file['submission'] = False

        try:
            # Second: register the file in the database
            yield register_ifile_on_db(uploaded_file, itip_id)
        except Exception as excep:
            log.err("Unable to register (append) file in DB: %s" % excep)
            print excep
            raise errors.InternalServerError("Unable to accept new files")


class FileInstance(BaseHandler):
    """
    WhistleBlower interface to upload a new file for an yet to be completed submission
    """
    handler_exec_time_threshold = 3600
    check_roles = 'unauthenticated'

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
