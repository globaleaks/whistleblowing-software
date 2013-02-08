# -*- coding: utf-8 -*-
#
#  files
#  *****
# 
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement

import os
from twisted.internet.defer import inlineCallbacks
from cyclone.web import HTTPError, asynchronous
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils import log
from globaleaks.config import config
from globaleaks.transactors.fileoperations import FileOperations
from globaleaks.rest.errors import SubmissionGusNotFound, InvalidInputFormat

__all__ = ['Download', 'FileInstance']

class FileInstance(BaseHandler):
    """
    U4

    This is the Storm interface to supports JQueryFileUploader stream
    """

    # Set to None for no size restrictions
    maxFileSize = 500 * 1000 * 1000 # MB

    def acceptedFileType(self, type):
        regexp = None
        if regexp and regexp.match(type):
            return True
        else:
            return False

    def validate(self, file):
        """
        Takes as input a file object and raises an exception if the file does
        not conform to the criteria.
        """
        if self.maxFileSize and file['size'] < self.maxFileSize:
            raise HTTPError(406, "File too big")

        if not self.acceptedFileType(file['type']):
            raise HTTPError(406, "File of unsupported type")



    @asynchronous
    @inlineCallbacks
    def get(self, submission_gus, *args):
        """
        Parameters: submission_gus
        Request: None
        Response: Unknown
        Errors: Unknown

        GET return list of files uploaded in this submission
        Doubt: Is this API needed ? because in JQueryFileUploader do not exists
            but in our GL-API-Style design could. At the moment the client
            do not plan to use them.
        """

        answer = yield FileOperations().get_files(submission_gus)

        self.write(answer['data'])
        self.set_status(200)

    @asynchronous
    @inlineCallbacks
    def post(self, submission_gus, *args):
        """
        Parameter: submission_gus
        Request: Unknown
        Response: Unknown
        Errors: SubmissionGusNotFound, SubmissionConcluded
        """

        try:
            answer = yield FileOperations().new_files(submission_gus, self.request)

            self.write(answer['data'])
            self.set_status(answer['code'])

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_message})

        except SubmissionGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_message})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, submission_gus, *args):
        """
        Request: Unknown
        Response: Unknown
        Errors: Unknown

        DELETE in fileHandlers need to be refactored-engineered
        """
        print self.request
        print submission_gus
        Exception("Not Yet Implemented file delete")


class Download(BaseHandler):
    """
    Not yet implemented download
    """

    @asynchronous
    @inlineCallbacks
    def get(self, file_gus):

        filelocation = os.path.join(config.advanced.submissions_dir, file_gus)

        file_iface = File()

        requestedfileinfo = yield file_iface.get_single(file_gus)


        print "Download of", requestedfileinfo

        self.render(filelocation, missing=[], info={
            "name": requestedfileinfo['name'],
            "file": "%s, type=%s, size=%s" % \
                    (str(requestedfileinfo['name']), str(requestedfileinfo['content_type']), str(requestedfileinfo['size']))
            }
        )



