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

from twisted.internet import fdesc
from cyclone.web import os
from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import GLSetting, transact
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.utils import log
from globaleaks.rest import errors
from globaleaks.rest.base import uuid_regexp
from globaleaks.models import Receiver


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
            '_gl_file_path': single_file['_gl_file_path'],
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
        filelocation = single_file['_gl_file_path']

        if os.path.exists(filelocation):
            log.err("Path %s exists and would be overwritten with %d bytes" %
                (filelocation, len(single_file['body']) ) )
        else:
            log.debug("Creating %s with %d bytes" %
                (filelocation, len(single_file['body']) ) )

        with open(filelocation, 'w+') as fd:
            fdesc.writeToFD(fd.fileno(), single_file['body'])

    return get_files_info(filesinupload)

def reserved_name_check(target_string):
    """
    @param target_string: its a string,

      This function is used for two different reasons:

        1) from the URI query, because if is present and match a reserved
           pattern, than is because Admin want trigger a special behavior
        2) from file upload data, because filename with reserved name need to
           be deny

    @return: True if a match is found, False if not.
    """
    reserved_logo_namel = len(GLSetting.reserved_nodelogo_name)
    if target_string[:reserved_logo_namel] == GLSetting.reserved_nodelogo_name:
        if len(target_string) > reserved_logo_namel:
            raise errors.ReservedFileName
        return True

    # an UUID is long 36 byte
    if re.match(uuid_regexp, target_string[:36]):
        if len(target_string) > 36:
            raise errors.ReservedFileName
        return True

    return False

def import_node_logo(filedesc):
    """
    @param filedesc: a dict with 'filename', 'content_type' and 'size' keys

    This function, just move the received file to globaleaks_logo.png
    At the moment do not check content-type validity nor perform resize.

    This change has been introduced for the tickets:
    https://github.com/globaleaks/GlobaLeaks/issues/246
    https://github.com/globaleaks/GlobaLeaks/issues/146
    https://github.com/globaleaks/GlobaLeaks/issues/247

    TODO, introduce a check that verify file is an Image ?
    https://github.com/globaleaks/GlobaLeaks/issues/298
    still we need a library to assign the right content-type

    """
    logopath = os.path.join(GLSetting.static_path, "%s.png" % GLSetting.reserved_nodelogo_name)

    try:
        if os.path.isfile(logopath):
            os.unlink(logopath)

        os.rename(filedesc['_gl_file_path'], logopath)
    except Exception as excep:
        log.err("OS Error in moving received file to be node logo! %s" % excep.message)
        raise excep

    log.debug("Moved received file %s [%d bytes] with path: %s " %
              (filedesc['filename'], filedesc['size'], logopath) )


@transact
def import_receiver_pic(store, filedesc, receiver_uuid):
    """
    @param filedesc: a dict with 'filename', 'content_type' and 'size' keys

    This function, just move the received file to $UUID.png
    At the moment do not check content-type validity nor perform resize.

    This change has been introduced for the tickets:
    https://github.com/globaleaks/GlobaLeaks/issues/246
    https://github.com/globaleaks/GlobaLeaks/issues/146
    https://github.com/globaleaks/GlobaLeaks/issues/247

    """
    receiver = store.find(Receiver, Receiver.id == unicode(receiver_uuid)).one()
    if not receiver:
        raise errors.ReceiverGusNotFound

    receiver_pic = os.path.join(GLSetting.static_path, "%s.png" % receiver_uuid)

    try:
        if os.path.isfile(receiver_pic):
            os.unlink(receiver_pic)

        os.rename(filedesc['_gl_file_path'], receiver_pic)
    except Exception as excep:
        log.err("OS Error in moving received file to be receiver portrait! %s" % excep.message)
        raise excep

    log.debug("Moved received file %s [%d bytes] for user %s with path: %s " %
              (filedesc['filename'], filedesc['size'], receiver.username, receiver_pic) )

    return receiver.name


class StaticFileCollection(BaseHandler):
    """
    Complete CRUD implementation using the filename instead of UUIDs
    """

    @inlineCallbacks
    @transport_security_check('admin')
    @authenticated('admin')
    def post(self, *args):
        """
        Upload a new files (one or more)
        """
        result_list = []
        start_time = time.time()

        if not self.request.files:
            raise errors.InvalidInputFormat("Missing POST elements")

        file_array, files = self.request.files.popitem()

        # Do not accept file with reserved filename
        try:
            for single_file_block in files:
                fname = single_file_block['filename']
                reserved_name = reserved_name_check(fname)
                if len(files) > 1 and reserved_name:
                    raise errors.ReservedFileName

                # not very clean, but files after this validation step has the path added
                # to the Cyclone request
                single_file_block['_gl_file_path'] =  os.path.join(GLSetting.static_path, fname)

        except Exception as excpd:
            log.err("Invalid stuff received: %s" % excpd)
            raise errors.InvalidInputFormat("filename is missing in uploaded file block")

        # First iterloop, dumps the files in the filesystem,
        # and exception raised here would prevent the InternalFile recordings
        try:
            file_list = dump_static_files(files)
        except OSError as excpd:
            inf_list = get_files_info(files)
            log.err("OSError while create a new static file [%s]: %s" % (str(inf_list), excpd))
            raise errors.InternalServerError(excpd.strerror)
        except Exception as excpd:
            log.err("Not handled exception: %s" % excpd.__repr__())
            raise errors.InternalServerError()

        for file_desc in file_list:
            log.debug("Admin uploaded new static file: %s" % file_desc['filename'] )
            file_desc['elapsed_time'] = time.time() - start_time
            result_list.append(file_desc)

        # checks if the file is single, and if special meaning is specified, in this case,
        # the original name of the file is changed with the appropriate one.
        if len(file_list) == 1 and reserved_name_check(self.request.query):

            specified_keyword = self.request.query
            selected_file = file_list[0]

            if specified_keyword == GLSetting.reserved_nodelogo_name:
                try:
                    import_node_logo(selected_file)
                    log.debug("Successful imported %s as new Node logo" % selected_file['filename'])
                except Exception as excpd:
                    log.err("Invalid Image Library operation [%s] with Node logo %s" %
                            (selected_file['filename'], excpd) )
                    raise errors.InternalServerError()
            else:
                try:
                    receiver_name = yield import_receiver_pic(selected_file, specified_keyword)
                    log.debug("Successful imported %s as portrait of %s" %
                              (selected_file['filename'], receiver_name) )
                except errors.ReceiverGusNotFound as excpd:
                    log.err("Invalid Receiver ID specified: %s" % specified_keyword)
                    raise excpd
                except Exception as excpd:
                    log.err("Invalid Image Library operation [%s] with Receiver %s portrait %s" %
                            (selected_file['filename'], specified_keyword, excpd) )
                    raise errors.InternalServerError()

        self.set_status(201) # Created
        self.finish(result_list)


    @transport_security_check('admin')
    @authenticated('admin')
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

    @transport_security_check('admin')
    @authenticated('admin')
    def delete(self, filename, *args):
        """
        Parameter: filename
        Errors: StaticFileNotFound
        """
        filelocation = os.path.join(GLSetting.static_path, filename)

        if not os.path.exists(filelocation):
            raise errors.StaticFileNotFound

        # XXX if a reserved filename is requested, need to be handled in
        # a safe way: eg, if is a receiver, restore the default image.
        os.unlink(filelocation)

        self.set_status(200)
        self.finish()
