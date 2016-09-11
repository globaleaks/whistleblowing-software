# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling static files upload/download/delete

from twisted.internet import threads
from cyclone.web import os
from twisted.internet.defer import inlineCallbacks
from globaleaks.settings import GLSettings
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils.utility import log
from globaleaks.rest import errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import directory_traversal_check

def get_description_by_stat(statstruct, name):
    return {
      'filename': name,
      'size': statstruct.st_size
    }


def get_stored_files():
    stored_list = []
    for fname in os.listdir(GLSettings.static_path):
        filepath = os.path.join(GLSettings.static_path, fname)
        if os.path.isfile(filepath):
            statinfo = os.stat(filepath)
            stored_list.append(get_description_by_stat(statinfo, fname))

    return stored_list


def get_file_info(uploaded_file, filelocation):
    """
    @param uploaded_file: the bulk of Cyclone upload data
           filelocation: the absolute path where the file goes
    @return: list of files with content_type and size.
    """
    return {
        'filename': uploaded_file['filename'],
         'content_type': uploaded_file['content_type'],
         'size': uploaded_file['body_len'],
         'filelocation': filelocation
    }


def dump_static_file(uploaded_file, filelocation):
    """
    @param uploadedfile: uploaded_file
    @return: a relationship dict linking the filename with the random
        filename saved in the disk
    """
    try:
        if os.path.exists(filelocation):
            log.err('Overwriting file %s with %d bytes' % (filelocation, uploaded_file['body_len']))
        else:
            log.debug('Creating file %s with %d bytes' % (filelocation, uploaded_file['body_len']))

        with open(filelocation, 'w+') as fd:
            uploaded_file['body'].seek(0, 0)
            data = uploaded_file['body'].read(4000)
            while data != '':
                os.write(fd.fileno(), data)
                data = uploaded_file['body'].read(4000)
    finally:
        uploaded_file['body'].close()

    return get_file_info(uploaded_file, filelocation)


class StaticFileInstance(BaseHandler):
    """
    Handler for files stored on the filesystem
    """
    handler_exec_time_threshold = 3600
    filehandler = True

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, filename):
        """
        Upload a new file
        """
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        if filename == 'upload':
            filename = uploaded_file['filename']

        path = os.path.join(GLSettings.static_path, filename)
        directory_traversal_check(GLSettings.static_path, path)

        try:
            dumped_file = yield threads.deferToThread(dump_static_file, uploaded_file, path)
        finally:
            uploaded_file['body'].close()

        log.debug('Admin uploaded new static file: %s' % dumped_file['filename'])
        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self, filename):
        """
        Parameter: filename
        Errors: StaticFileNotFound
        """
        path = os.path.join(GLSettings.static_path, filename)
        directory_traversal_check(GLSettings.static_path, path)
        if not os.path.exists(path):
            raise errors.StaticFileNotFound

        os.remove(path)


class StaticFileList(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def get(self):
        """
        Return the list of static files, with few filesystem info
        """
        self.write(get_stored_files())
