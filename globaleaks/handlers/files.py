# -*- coding: utf-8 -*-
#
#  files
#  *****
#
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement
import os
import time

import shutil

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks
from cyclone.web import StaticFileHandler

from globaleaks.settings import transact, transact_ro, GLSetting, stats_counter
from globaleaks.handlers.base import BaseHandler, BaseStaticFileHandler, anomaly_check
from globaleaks.handlers.authentication import transport_security_check, authenticated, unauthenticated
from globaleaks.utils.utility import log, pretty_date_time
from globaleaks.rest import errors
from globaleaks.models import ReceiverTip, ReceiverFile, InternalTip, InternalFile, WhistleblowerTip
from globaleaks.security import access_tip

def serialize_file(internalfile):

    file_desc = {
        'size' : internalfile.size,
        'content_type' : internalfile.content_type,
        'name' : internalfile.name,
        'creation_date': pretty_date_time(internalfile.creation_date),
        'id' : internalfile.id,
        'mark' : internalfile.mark,
    }

    return file_desc

def serialize_receiver_file(receiverfile):

    internalfile = receiverfile.internalfile

    file_desc = {
        'size' : receiverfile.size,
        'content_type' : internalfile.content_type,
        'name' : ("%s.pgp" % internalfile.name) if receiverfile.status == ReceiverFile._status_list[2] else internalfile.name,
        'creation_date': pretty_date_time(internalfile.creation_date),
        'downloads' : receiverfile.downloads,
        'path' : receiverfile.file_path,
    }

    return file_desc

@transact
def register_file_db(store, uploaded_file, filepath, internaltip_id):
    internaltip = store.find(InternalTip,
                             InternalTip.id == internaltip_id).one()

    if not internaltip:
        log.err("File submission register in a submission that's no more")
        raise errors.TipIdNotFound

    new_file = InternalFile()
    new_file.name = uploaded_file['filename']
    new_file.description = ""
    new_file.content_type = uploaded_file['content_type']
    new_file.mark = InternalFile._marker[0] # 'not processed'
    new_file.size = uploaded_file['body_len']
    new_file.internaltip_id = unicode(internaltip_id)
    new_file.file_path = filepath

    store.add(new_file)

    log.debug("=> Recorded new InternalFile %s" % uploaded_file['filename'])

    return serialize_file(new_file)


def dump_file_fs(uploaded_file):
    """
    @param files: a file
    @return: a filepath linking the filename with the random
             filename saved in the disk
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
    return encrypted_destination


@transact_ro
def get_tip_by_submission(store, itip_id):

    itip = store.find(InternalTip,
                      InternalTip.id == itip_id).one()

    if not itip:
        raise errors.SubmissionIdNotFound

    if itip.mark != InternalTip._marker[0]:
        log.err("Denied access on a concluded submission")
        raise errors.SubmissionConcluded
    else:
        return itip.id

@transact_ro
def get_tip_by_wbtip(store, wb_tip_id):

    wb_tip = store.find(WhistleblowerTip,
                        WhistleblowerTip.id == wb_tip_id).one()

    if not wb_tip:
        raise errors.InvalidTipAuthToken

    return wb_tip.internaltip.id


class FileHandler(BaseHandler):

    @inlineCallbacks
    def handle_file_upload(self, itip_id):
        result_list = []

        # measure the operation of all the files (via browser can be selected
        # more than 1), because all files are delivered in the same time.
        start_time = time.time()

        uploaded_file = self.request.body

        uploaded_file['body'].avoid_delete()
        uploaded_file['body'].close()

        try:
            # First: dump the file in the filesystem,
            # and exception raised here would prevent the InternalFile recordings
            filepath = yield threads.deferToThread(dump_file_fs, uploaded_file)
        except Exception as excep:
            log.err("Unable to save a file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")
        try:
            # Second: register the file in the database
            registered_file = yield register_file_db(uploaded_file, filepath, itip_id)
        except Exception as excep:
            log.err("Unable to register file in DB: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")

        registered_file['elapsed_time'] = time.time() - start_time
        result_list.append(registered_file)

        self.set_status(201) # Created
        self.write({'files': result_list})


# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(FileHandler):
    """
    WhistleBlower interface for upload a new file in an already completed submission
    """

    @transport_security_check('wb')
    @authenticated('wb')
    @anomaly_check('file_uploaded')
    @inlineCallbacks
    def post(self, *args):
        """
        Request: Unknown
        Response: Unknown
        Errors: TipIdNotFound
        """
        stats_counter('file_uploaded')
        itip_id = yield get_tip_by_wbtip(self.current_user['user_id'])

        # Call the master class method
        yield self.handle_file_upload(itip_id)

class FileInstance(FileHandler):
    """
    WhistleBlower interface for upload a new file in a not yet completed submission
    """

    @transport_security_check('wb')
    @unauthenticated
    @anomaly_check('file_uploaded')
    @inlineCallbacks
    def post(self, submission_id, *args):
        """
        Parameter: internaltip_id
        Request: Unknown
        Response: Unknown
        Errors: SubmissionIdNotFound, SubmissionConcluded
        """
        stats_counter('file_uploaded')
        itip_id = yield get_tip_by_submission(submission_id)

        # Call the master class method
        yield self.handle_file_upload(itip_id)


@transact
def download_file(store, user_id, tip_id, file_id):
    """
    Auth temporary disabled, just Tip_id and File_id required
    """

    rtip = access_tip(store, user_id, tip_id)

    rfile = store.find(ReceiverFile,
                       ReceiverFile.id == unicode(file_id)).one()

    if not rfile or rfile.receiver_id != user_id:
        raise errors.FileIdNotFound

    log.debug("Download of %s: %d of %d for %s" %
              (rfile.internalfile.name, rfile.downloads,
               rfile.internalfile.internaltip.download_limit, rfile.receiver.name))

    if rfile.downloads == rfile.internalfile.internaltip.download_limit:
        raise errors.DownloadLimitExceeded

    rfile.downloads += 1

    return serialize_receiver_file(rfile)


@transact
def download_all_files(store, user_id, tip_id):

    rtip = access_tip(store, user_id, tip_id)

    rfiles = store.find(ReceiverFile,
                        ReceiverFile.receiver_tip_id == unicode(tip_id))

    files_list = []
    for sf in rfiles:

        if sf.downloads == sf.internalfile.internaltip.download_limit:
            log.debug("massive file download for %s: skipped %s (limit %d reached)" % (
                sf.receiver.name, sf.internalfile.name, sf.downloads
            ))
            continue

        sf.downloads += 1
        files_list.append(serialize_receiver_file(sf))

    return files_list


class Download(BaseHandler):

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, tip_id, rfile_id, *uriargs):

        rfile = yield download_file(self.current_user.user_id, tip_id, rfile_id)

        # keys:  'file_path'  'size' : 'content_type' 'file_name'

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Length', rfile['size'])
        self.set_header('Content-Disposition','attachment; filename=\"%s\"' % rfile['name'])

        filelocation = os.path.join(GLSetting.submission_path, rfile['path'])

        try:

            with open(filelocation, "rb") as requestf:
                chunk_size = 8192
                while True:
                    chunk = requestf.read(chunk_size)
                    if len(chunk) == 0:
                        break
                    self.write(chunk)

        except IOError as srcerr:
            log.err("Unable to open %s: %s " % (filelocation, srcerr.strerror))
            self.set_status(404)

        self.finish()
