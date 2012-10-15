# -*- coding: utf-8 -*-
#
# jQuery File Upload Plugin cyclone example
# by Arturo Filastò <arturo@filasto.net>
#

from __future__ import with_statement

from globaleaks import models

from twisted.internet.defer import inlineCallbacks
from cyclone.web import RequestHandler, HTTPError, asynchronous

import json, re, urllib
import time, hashlib
import sys, os

listen_port = 8888

class FilesHandler(RequestHandler):
    filenamePrefix = "cyclone_upload_"
    # Set to None for no size restrictions
    maxFileSize = 500 * 1000 * 1000 # MB

    def acceptedFileType(self, type):
        regexp = None
        # regexp = re.compile('image/(gif|p?jpeg|(x-)?png)')
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
        with open(filelocation, 'w+') as f:
            f.write(data)

    def process_file(self, file):
        filename = re.sub(r'^.*\\', '', file['filename'])

        result = {}
        result['name'] = filename
        result['type'] = file['content_type']
        result['size'] = len(file['body'])

        filelocation = self.getFileLocation(filename)
        filetoken = self.getFileToken(filelocation)

        result['token'] = filetoken

        self.saveFile(file['body'], filelocation)
        return result

    def getFileToken(self, filelocation):
        """
        Ovewrite this with a function that returns the token to be given to the
        user for accessing the file.
        """
        return filelocation

    def getFileLocation(self, filename):
        """
        Ovewrite me with your own function to generate the location of where
        the file should be stored.
        """
        rname = hashlib.sha256(filename).hexdigest()
        name = self.filenamePrefix+rname+'.file'
        return name

    def options(self):
        pass

    def head(self):
        pass

    def get(self, *arg, **kw):
        pass

    @asynchronous
    @inlineCallbacks
    def post(self, submission_id):
        method_hack = self.get_arguments('_method')
        if method_hack and method_hack == 'DELETE':
            self.delete()

        results = []

        # XXX will this ever be bigger than 1?
        file_array, files = self.request.files.popitem()
        for file in files:
            print "Processing %s" % file
            start_time = time.time()
            result = self.process_file(file)
            result['elapsed_time'] = time.time() - start_time
            results.append(result)

            submission = models.submission.Submission()
            yield submission.add_file(submission_id, result['name'])

        response = json.dumps(results, separators=(',',':'))

        if 'application/json' in self.request.headers.get('Accept'):
            self.set_header('Content-Type', 'application/json')
        self.write(response)

    def delete(self):
        pass

