# -*- coding: utf-8 -*-
#
#  files
#  *****
#
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement
import time

from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks
from cyclone.web import os

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated, unauthenticated
from globaleaks.utils import log, pretty_date_time
from globaleaks.rest import errors
from globaleaks.models import ReceiverFile, ReceiverTip, InternalTip, InternalFile, WhistleblowerTip
from globaleaks.third_party import rstr


__all__ = ['Download', 'FileInstance']

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

@transact
def register_file_db(store, uploaded_file, filepath, internaltip_id):
    internaltip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

    if not internaltip:
        log.err("File submission register in a submission that's no more")
        raise errors.TipGusNotFound

    original_fname = uploaded_file['filename']

    try:
        new_file = InternalFile()

        new_file.name = original_fname
        new_file.content_type = uploaded_file['content_type']
        new_file.mark = InternalFile._marker[0]
        new_file.size = uploaded_file['body_len']
        new_file.internaltip_id = unicode(internaltip_id)
        new_file.file_path = filepath

        store.add(new_file)
        store.commit()
    except Exception as excep:
        log.err("Unable to commit new InternalFile %s: %s" % (original_fname.encode('utf-8'), excep))
        raise excep

    # I'm forcing commits because I've got some inconsistencies
    # in this ReferenceSets. need to be investigated if needed.
    try:
        #internaltip.internalfiles.add(new_file)
        store.commit()
    except Exception as excep:
        log.err("Unable to reference InternalFile %s in InternalTip: %s" % (original_fname, excep))
        raise excep

    log.debug("Added to the DB, file %s" % original_fname)

    return serialize_file(new_file)


def dump_file_fs(uploaded_file):
    """
    @param files: a file
    @return: a filepath linking the filename with the random
             filename saved in the disk
    """
    from Crypto.Random import atfork
    atfork()

    saved_name = rstr.xeger(r'[A-Za-z]{26}')
    filelocation = os.path.join(GLSetting.submission_path, saved_name)

    log.debug("Start saving %d bytes from file [%s]" %
              (uploaded_file['body_len'], uploaded_file['filename'].encode('utf-8')))

    with open(filelocation, 'w+') as fd:
        uploaded_file['body'].seek(0, 0)
        data = uploaded_file['body'].read() # 4kb
        total_length = 0
        while data != "":
            total_length += len(data)
            os.write(fd.fileno(), data)
            data = uploaded_file['body'].read(4096) # 4kb

    return saved_name

@transact_ro
def get_tip_by_submission(store, id):

    try:
        itip = store.find(InternalTip, InternalTip.id == unicode(id)).one()
    except Exception as excep:
        log.err("get_tip_by_submission: Error in store.find: %s" % excep)
        raise errors.SubmissionGusNotFound

    if not itip:
        raise errors.SubmissionGusNotFound
    elif itip.mark != InternalTip._marker[0]:
        log.err("Denied access on a concluded submission")
        raise errors.SubmissionConcluded
    else:
        return itip.id

@transact_ro
def get_tip_by_wbtip(store, wb_tip_id):

    try:
        wb_tip = store.find(WhistleblowerTip,
                            WhistleblowerTip.id == wb_tip_id).one()
    except Exception as excep:
        log.err("get_tip_by_wtipid, reference (1) is missing: %s" % excep)
        raise errors.SubmissionGusNotFound

    if not wb_tip:
        raise errors.InvalidTipAuthToken

    try:
        itip = store.find(InternalTip,
                          InternalTip.id == wb_tip.internaltip_id).one()
    except Exception as excep:
        log.err("get_tip_by_wtipid, reference (2) is missing: %s" % excep)
        raise errors.SubmissionGusNotFound

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

        uploaded_file = self.request.body

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


# This is different from FileInstance,just because there are a different authentication requirements
class FileAdd(FileHandler):
    """
    T4
    WhistleBlower interface for upload a new file in an already completed submission
    """

    @transport_security_check('tip')
    @authenticated('wb')
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
    WhistleBlower interface for upload a new file in a not yet completed submission
    """

    @transport_security_check('submission')
    @unauthenticated
    @inlineCallbacks
    def post(self, submission_id, *args):
        """
        Parameter: submission_gus
        Request: Unknown
        Response: Unknown
        Errors: SubmissionGusNotFound, SubmissionConcluded
        """
        itip_id = yield get_tip_by_submission(submission_id)

        # Call the master class method
        yield self.handle_file_upload(itip_id)


def serialize_receiver_file(receiverfile, internalfile):

    file_desc = {
        'size' : receiverfile.size,
        'content_type' : internalfile.content_type,
        'name' : ("%s.pgp" % internalfile.name) if receiverfile.status == ReceiverFile._status_list[2] else internalfile.name,
        'creation_date': pretty_date_time(internalfile.creation_date),
        'downloads' : receiverfile.downloads,
        'path' : receiverfile.file_path,
        'sha2sum' : internalfile.sha2sum,
    }
    return file_desc

@transact
def download_file(store, tip_id, file_id):
    """
    Auth temporary disabled, just Tip_id and File_id required
    """

    receivertip = store.find(ReceiverTip, ReceiverTip.id == unicode(tip_id)).one()
    if not receivertip:
        raise errors.TipGusNotFound

    file_obj = store.find(ReceiverFile, ReceiverFile.id == unicode(file_id)).one()
    if not file_obj:
        raise errors.FileGusNotFound

    log.debug("Download of %s downloads: %d with limit of %s for %s" %
              (file_obj.internalfile.name, file_obj.downloads,
               file_obj.internalfile.internaltip.download_limit, receivertip.receiver.name) )

    if file_obj.downloads == file_obj.internalfile.internaltip.download_limit:
        raise errors.DownloadLimitExceeded

    file_obj.downloads += 1

    return serialize_receiver_file(file_obj, file_obj.internalfile)


class Download(BaseHandler):

    @unauthenticated
    @inlineCallbacks
    def get(self, tip_gus, file_gus, *uriargs):

        # tip_gus needed to authorized the download

        file_details = yield download_file(tip_gus, file_gus)
        # keys:  'file_path'  'sha2sum'  'size' : 'content_type' 'file_name'

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Length', file_details['size'])
        self.set_header('Etag', '"%s"' % file_details['sha2sum'])
        self.set_header('Content-Disposition','attachment; filename=\"%s\"' % file_details['name'])

        filelocation = os.path.join(GLSetting.submission_path, file_details['path'])

        chunk_size = 8192
        filedata = ''
        with open(filelocation, "rb") as requestf:
            while True:
                chunk = requestf.read(chunk_size)
                filedata += chunk
                if len(chunk) == 0:
                    break

        self.write(filedata)
        self.finish()
