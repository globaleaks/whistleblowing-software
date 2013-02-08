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

        except (InvalidInputFormat, SubmissionGusNotFound) as error:
            self.write_error(error)

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

    @asynchronous
    @inlineCallbacks
    def get(self, file_gus, *uriargs):

        try:
            # tip_gus needed to authorized the download

            answer = yield FileOperations().download_file(file_gus)

            fileContent = answer['data']
            # keys:  'content'  'sha2sum'  'size' : 'content_type' 'file_name'

            self.set_status(answer['code'])

            self.set_header('Content-Type', fileContent['content_type'])
            self.set_header('Content-Length', fileContent['size'])
            self.set_header('Etag', '"%s"' % fileContent['sha2sum'])

            self.write(fileContent['content'])

        except (InvalidInputFormat) as error:
            self.write_error(error)

        self.finish()
