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
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.server import NOT_DONE_YET
from cyclone.web import os, StaticFileHandler
from Crypto.Hash import SHA256

from tempfile import TemporaryFile

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler, BaseStaticFileHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated, unauthenticated
from globaleaks.utils.utility import log, pretty_date_time
from globaleaks.utils.zipstream import ZipStream, ZIP_STORED, ZIP_DEFLATED
from globaleaks.rest import errors
from globaleaks.models import ReceiverFile, ReceiverTip, InternalTip, InternalFile, WhistleblowerTip
from globaleaks.third_party import rstr

def serialize_file(internalfile):

    file_desc = {
        'size' : internalfile.size,
        'content_type' : internalfile.content_type,
        'name' : internalfile.name,
        'creation_date': pretty_date_time(internalfile.creation_date),
        'id' : internalfile.id,
        'mark' : internalfile.mark,
        'sha2sum': internalfile.sha2sum,
    }

    return file_desc

@transact
def register_file_db(store, uploaded_file, filepath, cksum, internaltip_id):
    internaltip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

    if not internaltip:
        log.err("File submission register in a submission that's no more")
        raise errors.TipGusNotFound

    original_fname = uploaded_file['filename']

    try:
        new_file = InternalFile()

        new_file.name = original_fname
        new_file.content_type = uploaded_file['content_type']
        new_file.mark = InternalFile._marker[0] # 'not processed'
        new_file.sha2sum = cksum
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

    log.debug("=> Recorded new InternalFile %s (%s)" % (original_fname, cksum) )

    return serialize_file(new_file)


def dump_file_fs(uploaded_file):
    """
    @param files: a file
    @return: three variables:
        #0 a filepath linking the filename with the random
             filename saved in the disk
        #1 SHA256 checksum of the file
        #3 size in bytes of the files
    """
    from Crypto.Random import atfork
    atfork()

    saved_name = rstr.xeger(r'[A-Za-z]{26}')
    filelocation = os.path.join(GLSetting.submission_path, saved_name)

    log.debug("Start saving %d bytes from file [%s]" %
              (uploaded_file['body_len'], uploaded_file['filename'].encode('utf-8')))

    # checksum is computed here, because don't slow down the operation
    # enough to postpone in a scheduled job.
    # https://github.com/globaleaks/GlobaLeaks/issues/600

    sha = SHA256.new()
    with open(filelocation, 'w+') as fd:
        uploaded_file['body'].seek(0, 0)

        data = uploaded_file['body'].read() # 4kb
        total_length = 0

        while data != "":
            total_length = total_length + len(data)
            sha.update(data)
            os.write(fd.fileno(), data)
            data = uploaded_file['body'].read(4096) # 4kb

    return (saved_name, sha.hexdigest(), total_length)


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
            (filepath, cksum, size) = yield threads.deferToThread(dump_file_fs, uploaded_file)
        except Exception as excep:
            log.err("Unable to save a file in filesystem: %s" % excep)
            raise errors.InternalServerError("Unable to accept new files")

        # integrity check: has been saved the same amount of byte declared ?
        if size != uploaded_file['body_len']:
            raise errors.InternalServerError("File has been truncated (%d saved on %d bytes)" %
                                             (size, uploaded_file['body_len']))

        try:
            # Second: register the file in the database
            registered_file = yield register_file_db(uploaded_file, filepath, cksum, itip_id)
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

        with open(filelocation, "rb") as requestf:
            chunk_size = 8192
            while True:
                chunk = requestf.read(chunk_size)
                if len(chunk) == 0:
                    break
                self.write(chunk)

        self.finish()


@transact
def download_all_files(store, tip_id):

    receivertip = store.find(ReceiverTip, ReceiverTip.id == unicode(tip_id)).one()
    if not receivertip:
        raise errors.TipGusNotFound

    files = store.find(ReceiverFile, ReceiverFile.receiver_tip_id == unicode(tip_id))

    files_list = []
    for sf in files:

        if sf.downloads == sf.internalfile.internaltip.download_limit:
            log.debug("massive file download for %s: skipped %s (limit %d reached)" % (
                sf.receiver.name, sf.internalfile.name, sf.downloads
            ))
            continue

        sf.downloads += 1
        files_list.append( serialize_receiver_file(sf, sf.internalfile) )

    return files_list

class CollectionDownload(BaseHandler):

    @unauthenticated
    @inlineCallbacks
    def get(self, tip_gus, path="/zipstored", compression="zipstored"):
        if compression == 'zipstored':
            zip_compression_type = ZIP_STORED
            content_type='application/zip'
        elif compression == 'zipdeflated':
            zip_compression_type = ZIP_DEFLATED
            content_type = 'application/zip'
        else:
            # just to be sure; by the way
            # the regexp of rest/api.py should prevent this.
            raise errors.InvalidInputFormat

        files_dict = yield download_all_files(tip_gus)

        if not files_dict:
            raise errors.DownloadLimitExceeded

        info  = "This is an archive of files downloaded from a GlobaLeaks node\n"
        info += "[Some operational security tips will go here]\n\n"

        sha = SHA256.new()

        info += "%s%s%s%s%s\n" % ("Filename",
                                  " "*(40-len("Filename")),
                                  "Size (Bytes)",
                                  " "*(15-len("Size (Bytes)")),
                                  "SHA256")

        total_size = 0
        for filedesc in files_dict:

            sha.update(filedesc['name'])

            length1 = 40 - len(filedesc['name'])
            length2 = 15 - len(str(filedesc['size']))

            info += "%s%s%i%s%s\n" % (filedesc['name'],
                                      " "*length1,
                                      filedesc['size'],
                                      " "*length2,
                                      filedesc['sha2sum'])

            total_size += filedesc['size']

            filedesc['name'] = filedesc['name'].encode('utf-8')

            # Update all the path with the absolute path
            filedesc['path'] = os.path.join(GLSetting.submission_path, filedesc['path'])

        info += "\nTotal size is: %s Bytes" % total_size

        files_dict.append({ 'buf'  : info,
                            'name' : "COLLECTION_INFO.txt" })

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', content_type)
        self.set_header('Etag', '"%s"' % sha.hexdigest())
        self.set_header('Content-Disposition','attachment; filename=\"collection.zip\"')

        if compression in ['zipstored', 'zipdeflated']:
            for data in ZipStream(files_dict, zip_compression_type):
                self.write(data)

        self.finish()

class CSSStaticFileHandler(BaseStaticFileHandler):
    """
    This class is used to return the custom CSS file; 
    if the file is not present, 200 is returned with an empty content
    """

    @unauthenticated
    def get(self, path, include_body=True):
        self.set_header('Content-Type', 'text/css')
        path = self.parse_url_path(path)
        abspath = os.path.abspath(os.path.join(self.root, path))
        if os.path.isfile(abspath):
            StaticFileHandler.get(self, path, include_body)
        else:
            # empty CSS and avoid 404 error log
            self.set_status(200)
            self.finish()
