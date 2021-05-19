# -*- coding: utf-8 -*-
#
# Handler dealing with submissions file uploads and subsequent submissions attachments
import base64

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import serializers
from globaleaks.orm import transact
from globaleaks.utils.crypto import GCE
from globaleaks.utils.utility import datetime_now


@transact
def register_ifile_on_db(session, tid, internaltip_id, uploaded_file):
    """
    Register a file on the database

    :param session: An ORM session
    :param tid: A tenant id
    :param internaltip_id: A id of the submission on which attaching the file
    :param uploaded_file: A file to be attached
    :return: A descriptor of the file
    """
    now = datetime_now()

    itip = session.query(models.InternalTip) \
                  .filter(models.InternalTip.id == internaltip_id,
                          models.InternalTip.enable_attachments.is_(True),
                          models.InternalTip.status != 'closed',
                          models.InternalTip.tid == tid).one()

    itip.update_date = now
    itip.wb_last_access = now

    if itip.crypto_tip_pub_key:
        for k in ['name', 'type', 'size']:
            uploaded_file[k] = base64.b64encode(GCE.asymmetric_encrypt(itip.crypto_tip_pub_key, str(uploaded_file[k])))

    new_file = models.InternalFile()
    new_file.name = uploaded_file['name']
    new_file.content_type = uploaded_file['type']
    new_file.size = uploaded_file['size']
    new_file.internaltip_id = internaltip_id
    new_file.filename = uploaded_file['filename']
    new_file.submission = uploaded_file['submission']
    new_file.internaltip_id = internaltip_id

    session.add(new_file)

    return serializers.serialize_ifile(session, new_file)


class SubmissionAttachment(BaseHandler):
    """
    Whistleblower interface to upload a new file for a non-finalized submission
    """
    check_roles = 'any'
    upload_handler = True

    def post(self, submission_id):
        temp_submission = self.state.TempSubmissions.get(submission_id, None)
        if temp_submission is None:
            return

        self.uploaded_file['submission'] = True

        temp_submission.files.append(self.uploaded_file)


class PostSubmissionAttachment(SubmissionAttachment):
    """
    Whistleblower interface to upload a new file for an existing submission
    """
    check_roles = 'whistleblower'
    upload_handler = True

    def post(self):
        self.uploaded_file['submission'] = False

        return register_ifile_on_db(self.request.tid, self.session.user_id, self.uploaded_file)
