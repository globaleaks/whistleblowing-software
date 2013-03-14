# -*- coding: utf-8 -*-
#
#  admstaticfiles
#  **************
#
# Backend supports for jQuery File Uploader, and implementation of the
# file statically uploaded by the Admin, and exposed after in http://NODE/static path

#`This code differs from handlers/file.py because files here are not tracked in the DB

from __future__ import with_statement
import time

from twisted.internet import fdesc
from cyclone.web import os

from globaleaks.settings import GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils import log
from globaleaks.rest import errors


def get_description_by_stat(statstruct, name):
    stored_file_desc =  {
            'filename': name,
            'size': statstruct.st_size,
        }
    return stored_file_desc


def get_stored_files():
    stored_list = []
    storedfiles = os.listdir(GLSetting.static_path)

    for fname in storedfiles:
        filepath = os.path.join(GLSetting.static_path, fname)
        statinfo = os.stat(filepath)
        stored_list.append(get_description_by_stat(statinfo, fname))

    return stored_list


def get_files_info(filesinupload):
    """
    @param filesinupload: the bulk of Cyclone upload data
    @return: list of files with content_type and size.
    """
    files_list = []
    for single_file in filesinupload:
        file_desc = {
            'filename': single_file['filename'],
            'content_type': single_file['content_type'],
            'size': len(single_file['body']),
        }
        files_list.append(file_desc)

    return files_list


def dump_static_files(filesinupload):
    """
    @param files: files uploaded in Cyclone upload
    @return: a relationship dict linking the filename with the random
        filename saved in the disk
    """

    # if someone of this function return an Exception OSError, is catch by handler
    for single_file in filesinupload:
        filelocation = os.path.join(GLSetting.static_path, single_file['filename'])

        if os.path.exists(filelocation):
            if not GLSetting.staticfile_overwrite:
                raise errors.StaticFileExist(single_file['filename'])

        with open(filelocation, 'w+') as fd:
            fdesc.setNonBlocking(fd.fileno())
            fdesc.writeToFD(fd.fileno(), single_file['body'])

    return get_files_info(filesinupload)


class StaticFileCollection(BaseHandler):
    """
    Complete CRUD implementation using the filename instead of UUIDs
    """

    def post(self, *args):
        """
        Upload a new files (one or more)
        """

        result_list = []
        start_time = time.time()

        file_array, files = self.request.files.popitem()

        # First iterloop, dumps the files in the filesystem,
        # and exception raised here would prevent the InternalFile recordings
        try:
            file_list = dump_static_files(files)
        except OSError, e:
            inf_list = get_files_info(files)
            log.err("OSError while create a new static file [%s]: %s" % (str(inf_list), e))
            raise errors.InternalServerError

        for file_desc in file_list:
            file_desc['elapsed_time'] = time.time() - start_time
            result_list.append(file_desc)

        self.set_status(201) # Created
        self.finish(result_list)

    def get(self, *args):
        """
        Return the list of static files, with few filesystem info
        """

        self.set_status(200)
        self.finish(get_stored_files())



class StaticFileInstance(BaseHandler):
    """
    This interface do not support at the moment GET and PUT, because the only
    useful function in this case is the single deletion.
    """

    def delete(self, filename, *args):
        """
        Parameter: filename
        Errors: StaticFileNotFound
        """
        filelocation = os.path.join(GLSetting.static_path, filename)

        if not os.path.exists(filelocation):
            raise errors.StaticFileNotFound

        os.unlink(filelocation)

        self.set_status(200)
        self.finish()
