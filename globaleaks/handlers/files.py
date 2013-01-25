# -*- coding: utf-8 -*-
#
#  files
#  *****
# 
# Backend supports for jQuery File Uploader, and implementation of the
# classes executed when an HTTP client contact /files/* URI

from __future__ import with_statement

import json, os, time
from twisted.internet.defer import inlineCallbacks
from cyclone.web import HTTPError, asynchronous
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils import log
from globaleaks.config import config
from globaleaks.models.submission import Submission
from globaleaks.models.externaltip import File
from globaleaks.models.submission import Submission
from globaleaks.rest.errors import SubmissionGusNotFound, SubmissionConcluded, InvalidInputFormat

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

    def saveFile(self, data, filelocation):
        """
        XXX This is currently blocking. MUST be refactored to not be blocking
        otherwise we loose...
        """
        with open(filelocation, 'a+') as f:
            f.write(data)

    def process_file(self, file, submission_gus, file_gus):

        result = {}
        result['file_gus'] = file_gus
        result['name'] = file['filename']
        result['type'] = file['content_type']
        result['size'] = len(file['body'])

        # XXX verify this token what's is it
        result['token'] = submission_gus

        file_location = self.getFileLocation(file_gus)

        log.debug("Saving file to %s" % file_location)
        self.saveFile(file['body'], file_location)
        return result

    def getFileLocation(self, file_gus):
        """
        Ovewrite me with your own function to generate the location of where
        the file should be stored.
        """
        if not os.path.isdir(config.advanced.submissions_dir):
            log.debug("%s does not exist. Creating it." % config.advanced.submissions_dir)
            os.mkdir(config.advanced.submissions_dir)

        the_submission_dir = config.advanced.submissions_dir

        # this happen only at the first execution
        if not os.path.isdir(the_submission_dir):
            os.mkdir(the_submission_dir)

        location = os.path.join(the_submission_dir, file_gus)

        return location

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
        file_iface = File()

        filelist = yield file_iface.get_all_by_submission(submission_gus)

        self.write(json.dumps(filelist))
        self.set_status(200)

    @asynchronous
    @inlineCallbacks
    def post(self, submission_gus, *args):
        """
        Parameter: submission_gus
        Request: Unknown
        Response: Unknown
        Errors: SubmissionGusNotFound, SubmissionConcluded

        POST in fileHandlers need to be refactored-engineered
        """

        submission_iface = Submission()
        try:

            submission_desc = yield submission_iface.get_single(submission_gus)

            if submission_desc['finalize']:
                raise SubmissionConcluded

            results = []

            # XXX will this ever be bigger than 1?
            file_array, files = self.request.files.popitem()
            for file in files:
                start_time = time.time()

                file_request = { 'filename' : file.get('filename'),
                                 'content_type' : file.get('content_type'),
                                 'file_size' : len(file['body']),
                                 'submission_gus' : submission_gus,
                                 'context_gus' : submission_desc['context_gus'],
                                 'description' : ''
                        }

                print "file_request", file_request, "\n"

                file_iface = File()
                file_desc = yield file_iface.new(file_request)

                log.debug("Created file from %s with file_gus %s" % (file_request['filename'], file_desc['file_gus'] ))

                result = self.process_file(file, submission_gus, file_desc['file_gus'])
                result['elapsed_time'] = time.time() - start_time
                results.append(result)


            response = json.dumps(results, separators=(',',':'))

            if 'application/json' in self.request.headers.get('Accept'):
                self.set_header('Content-Type', 'application/json')

            self.set_status(200)
            self.write(response)

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



