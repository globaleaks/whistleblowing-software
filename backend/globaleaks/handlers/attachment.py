# -*- coding: utf-8 -*-
#
# Handler dealing with submissions file uploads and subsequent submissions attachments
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import serializers
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.security import directory_traversal_check
from globaleaks.settings import Settings
from globaleaks.utils.token import TokenList
from globaleaks.utils.utility import datetime_now


@transact
def register_ifile_on_db(session, tid, uploaded_file, internaltip_id):
    now = datetime_now()

    session.query(models.InternalTip) \
           .filter(models.InternalTip.id == internaltip_id, models.InternalTip.tid == tid) \
           .update({'update_date': now, 'wb_last_access': now})

    new_file = models.InternalFile()
    new_file.tid = tid
    new_file.name = uploaded_file['name']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.internaltip_id = internaltip_id
    new_file.submission = uploaded_file['submission']
    new_file.filename = uploaded_file['filename']
    session.add(new_file)

    return serializers.serialize_ifile(session, new_file)


class SubmissionAttachment(BaseHandler):
    """
    WhistleBlower interface to upload a new file for a non-finalized submission
    """
    check_roles = 'unauthenticated'
    upload_handler = True

    def post(self, token_id):
        token = TokenList.get(token_id)

        self.uploaded_file['submission'] = True

        token.associate_file(self.uploaded_file)


class PostSubmissionAttachment(SubmissionAttachment):
    """
    WhistleBlower interface to upload a new file for an existing submission
    """
    check_roles = 'whistleblower'
    upload_handler = True

    @inlineCallbacks
    def post(self):
        itip_id = (yield models.get(models.InternalTip.id,
                                    models.InternalTip.id==self.current_user.user_id,
                                    models.InternalTip.tid==self.request.tid))[0]

        self.uploaded_file['submission'] = False

        yield register_ifile_on_db(self.request.tid, self.uploaded_file, itip_id)
