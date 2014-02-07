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
import re

from twisted.internet import threads
from cyclone.web import os
from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSetting, transact_ro
from globaleaks.handlers.base import BaseHandler, BaseStaticFileHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.utils.utility import log
from globaleaks.rest import errors
from globaleaks.rest.requests import uuid_regexp, receiver_img_regexp
from globaleaks import models

from globaleaks.security import directory_traversal_check

def reserved_file_check(filename):
    """
    Return True if filename matchs a reserved filename, False instead.
    """
    if filename in [ 'globaleaks_logo.png',
                     'custom_stylesheet.css'
                   ]:
        return True

    if re.match(receiver_img_regexp, filename):
        return True

    return False

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

        if os.path.isfile(filepath) and not reserved_file_check(fname):
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
        'filelocation': filelocation,
    }


def dump_static_file(uploaded_file, filelocation):
    """
    @param files: files uploaded in Cyclone upload
    @return: a relationship dict linking the filename with the random
        filename saved in the disk
    """

    if os.path.exists(filelocation):
        log.err("Path %s exists and would be overwritten with %d bytes" %
            (filelocation, uploaded_file['body_len'] ) )
    else:
        log.debug("Creating %s with %d bytes" %
            (filelocation, uploaded_file['body_len'] ) )

    with open(filelocation, 'w+') as fd:
        uploaded_file['body'].seek(0, 0)
        data = uploaded_file['body'].read(4000) # 4kb
        while data != "":
            os.write(fd.fileno(), data)
            data = uploaded_file['body'].read(4000) # 4kb

    return get_file_info(uploaded_file, filelocation)


@transact_ro
def receiver_pic_path(store, receiver_uuid):
    receiver = store.find(models.Receiver, models.Receiver.id == unicode(receiver_uuid)).one()

    if not receiver:
        raise errors.ReceiverGusNotFound

    return os.path.join(GLSetting.static_path, "%s.png" % receiver_uuid)


class StaticFileInstance(BaseStaticFileHandler):
    """
    Complete CRUD implementation using the filename instead of UUIDs
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self, filename):
        """
        Upload a new file
        """
        start_time = time.time()

        uploaded_file = self.get_uploaded_file()

        # This handler allow to upload files inside globaleaks static directory
        #
        # There 4 possibilities allowed are:
        #
        #   1) the destination is == GLSetting.reserved_names.logo
        #   2) the destination is == GLSetting.reserved_names.cc
        #   3) the "destination+".png" does not match receiver_img_regexp
        #   4) the provided filename is a receiver uuid

        #if not reserved_name_check(filename, uploaded_file['filename']):
        #    raise errors.InvalidInputFormat("Unexpected name")

        # the 'filename' key present in the uploaded_file dict is ignored

        if filename == GLSetting.reserved_names.logo:
            try:
                path = os.path.join(GLSetting.static_path, "%s.png" % GLSetting.reserved_names.logo)
                log.debug("Received request to update Node logo with %s" % uploaded_file['filename'])
            except Exception as excpd:
                log.err("Exception raise saving Node logo: %s" % excpd)
                raise errors.InternalServerError(excpd.__repr__())

        elif filename == GLSetting.reserved_names.css:
            try:
                path = os.path.join(GLSetting.static_path, "%s.css" % GLSetting.reserved_names.css)
                log.debug("Received request to update custom CSS with %s" % uploaded_file['filename'])
            except Exception as excpd:
                log.err("Exception raise saving custom CSS: %s" % excpd)
                raise errors.InternalServerError(excpd.__repr__())

        elif filename == 'customization' and \
             not re.match(receiver_img_regexp, uploaded_file['filename'] + ".png"):
                path = os.path.join(GLSetting.static_path, uploaded_file['filename'])
                log.debug("Received request to save %s in path %s" %
                          (uploaded_file['filename'], path))
        else:
            try:
                path = yield receiver_pic_path(filename)
                log.debug("Received request to update Receiver portrait with %s" % filename)
            except errors.ReceiverGusNotFound as excpd:
                log.err("Invalid Receiver ID specified: %s" % filename)
                raise excpd
            except Exception as excpd:
                log.err("Exception raised while saving Receive portrait with %s: %s" %
                        (filename, excpd))
                raise errors.InternalServerError(excpd.__repr__())

        directory_traversal_check(GLSetting.static_path, path)

        try:
            # the dump of the file is done here in the latest stage to
            # avoid writing non tracked files on the file system in case of exceptions
            dumped_file = yield threads.deferToThread(dump_static_file, uploaded_file, path)
        except OSError as excpd:
            log.err("OSError while create a new static file [%s]: %s" % (path, excpd) )
            raise errors.InternalServerError(excpd.strerror)
        except Exception as excpd:
            log.err("Unexpected exception: %s" % excpd.message)
            raise errors.InternalServerError(excpd.message)

        dumped_file['elapsed_time'] = time.time() - start_time

        log.debug("Admin uploaded new static file: %s" % dumped_file['filename'])

        self.set_status(201) # Created
        self.finish(dumped_file)


    @transport_security_check('admin')
    @authenticated('admin')
    def delete(self, filename):
        """
        Parameter: filename
        Errors: StaticFileNotFound
        """
        path = os.path.join(GLSetting.static_path, filename)
        directory_traversal_check(GLSetting.static_path, path)

        if not os.path.exists(path):
            raise errors.StaticFileNotFound

        # XXX if a reserved filename is requested, need to be handled in
        # a safe way: eg, if is a receiver, restore the default image.
        os.remove(path)

        self.set_status(200)
        self.finish()

class StaticFileList(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    def get(self):
        """
        Return the list of static files, with few filesystem info
        """
        self.set_status(200)
        self.finish(get_stored_files())

