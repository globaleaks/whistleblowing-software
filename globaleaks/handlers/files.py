# -*- coding: utf-8 -*-
#
#  files
#  *****
#
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement
from twisted.internet import fdesc
from twisted.internet.defer import inlineCallbacks
from globaleaks.settings import transact
from cyclone.web import os
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils import log, gltime
from globaleaks import settings
from globaleaks.rest import errors
from globaleaks import models
import time

__all__ = ['Download', 'FileInstance']


SUBMISSION_DIR = os.path.join(settings.gldata_path, 'submission')


def serialize_file(internalfile):

    file_desc = {
        'size' : internalfile.size,
        'content_type' : internalfile.content_type,
        'name' : internalfile.name,
        'creation_date': gltime.prettyDateTime(internalfile.creation_date),
    }

    return file_desc


def dump_single_file(store, client_file_desc, internaltip_id):

    # compose file request as the dict expected in File._import_dict
    file_request = { 'name' : client_file_desc.get('filename'),
                     'content_type' : client_file_desc.get('content_type'),
                     'mark' : models.InternalFile._marker[0],
                     'size' : len(client_file_desc['body']),
                     'internaltip_id' : internaltip_id,
                     'sha2sum' : ''
                   }

    new_file = models.InternalFile(file_request)
    store.add(new_file)

    print "Created file from %s with file_gus %s" % (new_file.name, new_file.id)

    if not os.path.isdir(SUBMISSION_DIR):
        log.msg("%s does not exist. Creating it." %
                SUBMISSION_DIR)
        os.mkdir(SUBMISSION_DIR)

    filelocation = os.path.join(SUBMISSION_DIR, new_file.id)

    print 'Saving file "%s" of %s byte [%s] type, in %s' %\
          (new_file.name, new_file.size, new_file.content_type, filelocation )

    # *The file is complete*
    # because Cyclone cache them before pass to the handler.
    # This mean that need to be limited client and Cyclone side,
    # and we here can't track about incomplete file.
    with open(filelocation, 'w+') as fd:
        fdesc.setNonBlocking(fd.fileno())
        fdesc.writeToFD(fd.fileno(), client_file_desc['body'])

    return serialize_file(new_file)


@transact
def create_tip_file(store, receipt, filerequest):
    """
    Tip need to be Whistleblower authenticated
    """

    wbtip = store.find(models.WhistleblowerTip,
                       models.WhistleblowerTip.receipt == unicode(receipt)).one()

    if not wbtip:
        raise errors.ReceiptGusNotFound

    result_list = []

    file_array, files = filerequest.files.popitem()
    for single_file in files:

        start_time = time.time()
        result = dump_single_file(store, single_file, wbtip.internaltip.id)
        result['elapsed_time'] = time.time() - start_time

        result_list.append(result)

@transact
def create_submission_file(store, id, filerequest):

    itip = store.find(models.InternalTip,
                      models.InternalTip.id == unicode(id)).one()

    if not itip:
        raise errors.SubmissionGusNotFound

    if itip.mark != models.InternalTip._marker[0]:
        raise errors.SubmissionConcluded

    result_list = []

    file_array, files = filerequest.files.popitem()
    for single_file in files:

        start_time = time.time()
        result = dump_single_file(store, single_file, itip.id)
        result['elapsed_time'] = time.time() - start_time

        result_list.append(result)


# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(BaseHandler):
    """
    T4
    WhistleBlower interface for upload a new file
    """

    @inlineCallbacks
    def post(self, tip_id, *args):
        """
        Parameter: submission_gus
        Request: Unknown
        Response: Unknown
        Errors: SubmissionGusNotFound, SubmissionConcluded
        """

        if self.current_user['role'] != 'wb':
            raise errors.InvalidAuthRequest

        answer = yield create_tip_file(self.current_user['password'], self.request)
        self.set_status(201) # Created

        self.finish(answer)


class FileInstance(BaseHandler):
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

        answer = yield create_submission_file(submission_id, self.request)
        self.set_status(201) # Created

        self.finish(answer)


class Download(BaseHandler):

    """
    @inlineCallbacks
    def get(self, tip_gus, CYCLON_DIRT, file_gus, *uriargs):

        # tip_gus needed to authorized the download
        print tip_gus, file_gus

        answer = yield FileOperations().get_file_access(tip_gus, file_gus)

        # verify if receiver can, in fact, download the file, otherwise
        # raise DownloadLimitExceeded

        fileContent = answer['data']
        # keys:  'content'  'sha2sum'  'size' : 'content_type' 'file_name'

        self.set_status(answer['code'])

        self.set_header('Content-Type', fileContent['content_type'])
        self.set_header('Content-Length', fileContent['size'])
        self.set_header('Etag', '"%s"' % fileContent['sha2sum'])

        filelocation = os.path.join(settings.config.advanced.submissions_dir, file_gus)

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
    """
