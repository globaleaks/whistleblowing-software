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
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.utils.utility import log
from globaleaks.rest import errors
from globaleaks.rest.base import uuid_regexp
from globaleaks import models

from globaleaks.security import directory_traversal_check

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


def reserved_name_check(target_string, original_fname):
    """
    @param target_string: its a string,

      This function is used to test the requested name, and
      remove those that eventually shall bring anomalies.

    @return: True if a match is found, False if not.
        raise ReservedFileName if we don't like your parameter
    """
    image = False

    reserved_logo_namel = len(GLSetting.reserved_names.logo)
    if target_string[:reserved_logo_namel] == GLSetting.reserved_names.logo:
        if len(target_string) > reserved_logo_namel:
            raise errors.ReservedFileName
        image = True

    if re.match(uuid_regexp, target_string[:36]): # an UUID is long 36 bytes
        if len(target_string) > 36:
            raise errors.ReservedFileName
        image = True

    if image:
        if original_fname.lower().endswith(GLSetting.images_extensions):
            return True

        # Invalid format check: this is not the right way, but at the
        # moment we're not including any magic-* in fear of the code surface!
        log.debug("Invalid image extension in %s (permitted only %s)" %
                  (original_fname, GLSetting.images_extensions))
        raise errors.InvalidInputFormat("Extension not accepted between images")

    # If not image, check CSS
    reserved_css_namel = len(GLSetting.reserved_names.css)
    if target_string[:reserved_css_namel] == GLSetting.reserved_names.css:
        if len(target_string) > reserved_css_namel:
            raise errors.ReservedFileName

        if original_fname.lower().endswith(GLSetting.css_extensions):
            return True

        # Invalid format check: this is not the right way, but at the
        # moment we're not including any magic-* in fear of the code surface!
        log.debug("Invalid CSS extension in %s (permitted only %s)" %
                  (original_fname, GLSetting.css_extensions))
        raise errors.InvalidInputFormat("Extension not accepted for CSS")

    log.debug("Rejecting file request [%s] with original fname [%s]" %
              (target_string, original_fname) )
    return False


@transact_ro
def receiver_pic_path(store, receiver_uuid):
    receiver = store.find(models.Receiver, models.Receiver.id == unicode(receiver_uuid)).one()

    if not receiver:
        raise errors.ReceiverGusNotFound

    return os.path.join(GLSetting.static_path, "%s.png" % receiver_uuid)


class StaticFileInstance(BaseHandler):
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

        # currently the static file upload is used to handle only
        # images uploads for Node and for Receivers so that all the logic
        # is embedded here. As also a dirty Input Validation (because body is
        # a file stream, not a python dict, and we're not checking exactly
        # what's has been uploaded. this code is run only by admin, but: XXX remind

        if not reserved_name_check(filename, uploaded_file['filename']):
            raise errors.InvalidInputFormat("Unexpected name")

        # the 'filename' key present in the uploaded_file dict is ignored

        if filename == GLSetting.reserved_names.logo:
            try:
                gl_file_path = os.path.join(GLSetting.static_path, "%s.png" % GLSetting.reserved_names.logo)
                log.debug("Received request to update Node logo with %s" % uploaded_file['filename'])
            except Exception as excpd:
                log.err("Exception raise saving Node logo: %s" % excpd)
                raise errors.InternalServerError(excpd.__repr__())
        elif filename == GLSetting.reserved_names.css:
            try:
                gl_file_path = os.path.join(GLSetting.static_path, "%s.css" % GLSetting.reserved_names.css)
                log.debug("Received request to update custom CSS with %s" % uploaded_file['filename'])
            except Exception as excpd:
                log.err("Exception raise saving custom CSS: %s" % excpd)
                raise errors.InternalServerError(excpd.__repr__())
        else:
            try:
                gl_file_path = yield receiver_pic_path(filename)
                log.debug("Received request to update Receiver portrait with %s" % filename)
            except errors.ReceiverGusNotFound as excpd:
                log.err("Invalid Receiver ID specified: %s" % filename)
                raise excpd
            except Exception as excpd:
                log.err("Exception raised while saving Receive portrait with %s: %s" %
                        (filename, excpd))
                raise errors.InternalServerError(excpd.__repr__())

        try:
            # the dump of the file is done here in the latest stage to
            # avoid writing non tracked files on the file system in case of exceptions
            dumped_file = yield threads.deferToThread(dump_static_file, uploaded_file, gl_file_path)
        except OSError as excpd:
            log.err("OSError while create a new static file [%s]: %s" % (gl_file_path, excpd) )
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
    def get(self):
        """
        Return the list of static files, with few filesystem info
        """
        self.set_status(200)
        self.finish(get_stored_files())


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
