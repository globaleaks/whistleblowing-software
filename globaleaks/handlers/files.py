# -*- coding: utf-8 -*-
#
#  files
#  *****
#
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement
import time
import copy

from twisted.internet import fdesc
from twisted.internet.defer import inlineCallbacks
from cyclone.web import os

from globaleaks.settings import transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated
from globaleaks.utils import log, gltime
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
        'creation_date': gltime.prettyDateTime(internalfile.creation_date),
    }

    return file_desc



@transact
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

    filelocation = os.path.join(SUBMISSION_DIR, new_file.id)

    with open(filelocation, 'w+') as fd:
        fdesc.setNonBlocking(fd.fileno())
        fdesc.writeToFD(fd.fileno(), client_file_desc['body'])

    return serialize_file(new_file)


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
        return wbtip.internaltip.id



# This is different from FileInstance, just because there are a different authentication requirements
class FileAdd(BaseHandler):
    """
    T4
    WhistleBlower interface for upload a new file
    """
    @inlineCallbacks
    @authenticated('wb')
    def post(self, tip_id, *args):
        """
        Parameter: submission_gus
        Request: Unknown
        Response: Unknown
        Errors: SubmissionGusNotFound, SubmissionConcluded
        """
        itipid = yield get_tip_by_internaltip(tip_id)
        result_list = []

        file_array, files = self.request.files.popitem()
        for single_file in files:
            start_time = time.time()
            result = yield dump_single_file(single_file, itipid)
            result['elapsed_time'] = time.time() - start_time
            result_list.append(result)

        self.set_status(201) # Created

        self.write(result_list)


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
        result_list = []

        file_array, files = self.request.files.popitem()
        for single_file in files:
            start_time = time.time()
            result = yield dump_single_file(single_file, submission_id)
            result['elapsed_time'] = time.time() - start_time
            result_list.append(result)

        self.set_status(201) # Created
        self.write(result_list)


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
