# -*- coding: utf-8 -*-
#
# jQuery File Upload Plugin cyclone example
# by Arturo Filastò <arturo@filasto.net>
#

from __future__ import with_statement

import json, os, time
from twisted.internet.defer import inlineCallbacks
from cyclone.web import RequestHandler, HTTPError, asynchronous
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils import log
from globaleaks import models, config

class FileCrud(BaseHandler):
    """
    U5
    need a complete redesign with async Tip/Submission
    """

    log.debug("[D] %s %s " % (__file__, __name__), "Class FileCrud", "RequestHandler", RequestHandler)
    filenamePrefix = "f_"
    # Set to None for no size restrictions
    maxFileSize = 500 * 1000 * 1000 # MB

    def acceptedFileType(self, type):
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "acceptedFileType", "type", type)
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
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "validate", "file", file)
        if self.maxFileSize and file['size'] < self.maxFileSize:
            raise HTTPError(406, "File too big")

        if not self.acceptedFileType(file['type']):
            raise HTTPError(406, "File of unsupported type")

    def saveFile(self, data, filelocation):
        """
        XXX This is currently blocking. MUST be refactored to not be blocking
        otherwise we loose...
        """
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "savefile", "data", type(data), "filelocation", filelocation)
        with open(filelocation, 'a+') as f:
            f.write(data)

    def process_file(self, file, submission_id, file_id):
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "process_file", "file",type(file), "submission_id", submission_id, "file_id", file_id)

        result = {}
        result['name'] = file_id
        result['type'] = file['content_type']
        result['size'] = len(file['body'])

        file_location = self.getFileLocation(submission_id, file_id)
        filetoken = submission_id

        result['token'] = filetoken

        log.debug("Saving file to %s" % file_location)
        self.saveFile(file['body'], file_location)
        return result

    def getFileLocation(self, submission_id, file_id):
        """
        Ovewrite me with your own function to generate the location of where
        the file should be stored.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "getFileLocation", "submission_id", submission_id, "file_id", file_id)
        if not os.path.isdir(config.advanced.submissions_dir):
            log.debug("%s does not exist. Creating it." % config.advanced.submissions_dir)
            os.mkdir(config.advanced.submissions_dir)

        this_submission_dir = os.path.join(config.advanced.submissions_dir, submission_id)

        if not os.path.isdir(this_submission_dir):
            log.debug("%s does not exist. Creating it." % this_submission_dir)
            os.mkdir(this_submission_dir)

        location = os.path.join(this_submission_dir, file_id)
        return location

    def options(self):
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "options")
        pass

    def head(self):
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "head")
        pass

    @asynchronous
    @inlineCallbacks
    def get(self, *arg, **kw):
        """
        Parameters: Unknown
        Request: None
        Response: Unknown
        Errors: Unknown

        GET in fileHandlers need to be refactored-engineered
        """
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "get")
        pass

    @asynchronous
    @inlineCallbacks
    def post(self, submission_id):
        """
        Request: Unknown
        Response: Unknown
        Errors: Unknown

        POST in fileHandlers need to be refactored-engineered
        """
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "post", "submission_id", submission_id)
        method_hack = self.get_arguments('_method')
        if method_hack and method_hack == 'DELETE':
            self.delete()

        results = []

        # XXX will this ever be bigger than 1?
        file_array, files = self.request.files.popitem()
        for file in files:
            start_time = time.time()

            submission = models.submission.Submission()
            file_id = yield submission.add_file(submission_id)
            log.debug("Created file with file id %s" % file_id)
            result = self.process_file(file, submission_id, file_id)
            result['elapsed_time'] = time.time() - start_time
            results.append(result)


        response = json.dumps(results, separators=(',',':'))

        if 'application/json' in self.request.headers.get('Accept'):
            self.set_header('Content-Type', 'application/json')
        self.write(response)
        self.finish()

    @asynchronous
    @inlineCallbacks
    def delete(self):
        """
        Request: Unknown
        Response: Unknown
        Errors: Unknown

        DELETE in fileHandlers need to be refactored-engineered
        """
        log.debug("[D] %s %s " % (__file__, __name__), "FilesHandler", "delete")
        pass

