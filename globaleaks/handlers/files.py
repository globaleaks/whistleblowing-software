# -*- coding: utf-8 -*-
#
#  files
#  *****
#
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement
import time

from twisted.internet import fdesc
from twisted.internet.defer import inlineCallbacks
from cyclone.web import os

from globaleaks.settings import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated
from globaleaks.utils import log, prettyDateTime, random_string
from globaleaks import settings
from globaleaks.rest import errors
from globaleaks import models

__all__ = ['Download', 'FileInstance']


SUBMISSION_DIR = os.path.join(settings.gldata_path, 'submission')
if not os.path.isdir(SUBMISSION_DIR):
    os.mkdir(SUBMISSION_DIR)


def serialize_file(internalfile):

    file_desc = {
        'size' : internalfile.size,
        'content_type' : internalfile.content_type,
        'name' : internalfile.name,
        'creation_date': prettyDateTime(internalfile.creation_date),
        'id' : internalfile.id,
        'mark' : internalfile.mark,
    }

    return file_desc

@transact
def register_files_db(store, files, relationship, internaltip_id):
    internaltip = store.find(models.InternalTip, models.InternalTip.id == internaltip_id).one()

    files_list = []
    for single_file in files:
        original_fname = single_file['filename']

        new_file = models.InternalFile()

        new_file.name = original_fname
        new_file.content_type = single_file.get('content_type')
        new_file.mark = unicode(models.InternalFile._marker[0])
        new_file.size = len(single_file['body'])
        new_file.internaltip_id = unicode(internaltip_id)
        new_file.file_path = relationship[original_fname]

        store.add(new_file)
        internaltip.internalfiles.add(new_file)
        files_list.append(serialize_file(new_file))

    return files_list

def dump_files_fs(files):
    """
    @param files: files uploaded in Cyclone upload
    @return: a relationship dict linking the filename with the random
        filename saved in the disk
    """
    files_saved = {}
    for single_file in files:
        saved_name = random_string(26, 'A-Z,a-z,0-9')
        filelocation = os.path.join(SUBMISSION_DIR, saved_name)

        with open(filelocation, 'w+') as fd:
            fdesc.setNonBlocking(fd.fileno())
            fdesc.writeToFD(fd.fileno(), single_file['body'])

        files_saved.update({single_file['filename']: saved_name })

    return files_saved


@transact
def get_tip_by_receipe(store, receipt):
    """
    Tip need to be Whistleblower authenticated
    """
    wbtip = store.find(models.WhistleblowerTip,
                       models.WhistleblowerTip.receipt == unicode(receipt)).one()
    if not wbtip:
        raise errors.ReceiptGusNotFound
    else:
        return wbtip.id

@transact
def get_tip_by_internaltip(store, id):
    itip = store.find(models.InternalTip,
                      models.InternalTip.id == unicode(id)).one()
    if not itip:
        raise errors.SubmissionGusNotFound
    elif itip.mark != models.InternalTip._marker[0]:
        raise errors.SubmissionConcluded
    else:
        return itip.id

@transact
def get_tip_by_wbtip(store, wb_tip_id):
    wb_tip = store.find(models.WhistleblowerTip,
                        models.WhistleblowerTip.id == wb_tip_id).one()

    if not wb_tip:
        raise errors.InvalidTipAuthToken

    itip = store.find(models.InternalTip,
                      models.InternalTip.id == unicode(wb_tip.internaltip_id)).one()
    if not itip:
        raise errors.SubmissionGusNotFound
    else:
        return itip.id

class FileHandler(BaseHandler):

    @inlineCallbacks
    def handle_file_upload(self, itip_id):
        result_list = []

        # measure the operation of all the files (via browser can be selected
        # more than 1), because all files are delivered in the same time.
        start_time = time.time()

        file_array, files = self.request.files.popitem()

        # First iterloop, dumps the files in the filesystem,
        # and exception raised here would prevent the InternalFile recordings
        try:
            relationship = dump_files_fs(files)
        except OSError, e:
            # TODO danger error log: unable to save in FS
            raise errors.InternalServerError

        # Second iterloop, create the objects in the database
        file_list = yield register_files_db(files, relationship, itip_id)

        for file_desc in file_list:
            file_desc['elapsed_time'] = time.time() - start_time
            result_list.append(file_desc)

        self.set_status(201) # Created
        self.write(result_list)

# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(FileHandler):
    """
    T4
    WhistleBlower interface for upload a new file
    """

    @inlineCallbacks
    def post(self, wb_tip_id, *args):
        """
        Parameter: submission_gus
        Request: Unknown
        Response: Unknown
        Errors: SubmissionGusNotFound, SubmissionConcluded
        """
        itip_id = yield get_tip_by_wbtip(wb_tip_id)

        # Call the master class method
        yield self.handle_file_upload(itip_id)

class FileInstance(FileHandler):
    """
    U4
    This is the Storm interface to supports JQueryFileUploader stream
    """

    @inlineCallbacks
    def post(self, submission_id, *args):
        """
        Parameter: submission_gus
        Request: Unknown
        Response: Unknown
        Errors: SubmissionGusNotFound, SubmissionConcluded
        """
        itip_id = yield get_tip_by_internaltip(submission_id)

        # Call the master class method
        yield self.handle_file_upload(itip_id)


def serialize_receiver_file(receiverfile, internalfile):

    file_desc = {
        'size' : internalfile.size,
        'content_type' : internalfile.content_type,
        'name' : internalfile.name,
        'creation_date': prettyDateTime(internalfile.creation_date),
        'downloads' : receiverfile.downloads,
        'path' : internalfile.file_path if internalfile.file_path else receiverfile.file_path,
        'sha2sum' : internalfile.sha2sum,
    }
    return file_desc

@transact
def download_file(store, tip_id, file_id):
    """
    Auth temporarly disabled, just Tip_id and File_id required
    """

    receivertip = store.find(models.ReceiverTip, models.ReceiverTip.id == unicode(tip_id)).one()
    if not receivertip:
        raise errors.TipGusNotFound

    file = store.find(models.ReceiverFile, models.ReceiverFile.id == unicode(file_id)).one()
    if not file:
        raise errors.FileGusNotFound

    log.debug("Download of %s downloads: %d with limit of %s for %s" %
              (file.internalfile.name, file.downloads,
               file.internalfile.internaltip.download_limit, receivertip.receiver.name) )

    if file.downloads == file.internalfile.internaltip.download_limit:
        raise errors.DownloadLimitExceeded

    file.downloads += 1

    return serialize_receiver_file(file, file.internalfile)


class Download(BaseHandler):

    @inlineCallbacks
    def get(self, tip_gus, file_gus, *uriargs):

        # tip_gus needed to authorized the download
        print "Access to: tip_id", tip_gus, "file_id", file_gus

        file_details = yield download_file(tip_gus, file_gus)
        # keys:  'file_path'  'sha2sum'  'size' : 'content_type' 'file_name'

        self.set_status(200)

        self.set_header('Content-Type', file_details['content_type'])
        self.set_header('Content-Length', file_details['size'])
        self.set_header('Etag', '"%s"' % file_details['sha2sum'])
        self.set_header('Content-Disposition','attachment; filename=\"%s\"' % file_details['name'])

        filelocation = os.path.join(SUBMISSION_DIR, file_details['path'])

        chunk_size = 8192
        filedata = ''
        with open(filelocation, "rb") as requestf:
            fdesc.setNonBlocking(requestf.fileno())
            while True:
                chunk = requestf.read(chunk_size)
                filedata += chunk
                if len(chunk) == 0:
                    break

        self.write(filedata)
        self.finish()
