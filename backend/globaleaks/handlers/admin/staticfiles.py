# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling static files upload/download/delete
import os

from twisted.internet import threads

from globaleaks.handlers.base import BaseHandler, write_upload_plaintext_to_disk
from globaleaks.rest import errors
from globaleaks.security import directory_traversal_check
from globaleaks.settings import GLSettings


def get_description_by_stat(statstruct, name):
    return {
      'name': name,
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


class StaticFileInstance(BaseHandler):
    """
    Handler for files stored on the filesystem
    """
    check_roles = 'admin'

    handler_exec_time_threshold = 3600

    def post(self, filename):
        """
        Upload a new file
        """
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        if filename == 'upload':
            filename = uploaded_file['name']

        path = os.path.join(GLSettings.static_path, filename)
        directory_traversal_check(GLSettings.static_path, path)

        d = threads.deferToThread(write_upload_plaintext_to_disk, uploaded_file, path)
        d.addBoth(lambda ignore: uploaded_file['body'].close)
        return d

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
    check_roles = 'admin'

    def get(self):
        """
        Return the list of static files, with few filesystem info
        """
        return get_stored_files()
