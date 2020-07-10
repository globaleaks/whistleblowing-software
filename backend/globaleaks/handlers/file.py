# -*- coding: utf-8 -*-
#
# Handlers exposing customization files
import base64
import os

from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.admin.file import db_get_file
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact, tw


appfiles = {
    'favicon': 'image/x-icon',
    'logo': 'image/png',
    'css': 'text/css',
    'script': 'application/javascript'
}


def db_mark_file_for_secure_deletion(session, directory, filename):
    """
    Transaction for marking a file for secure deletion

    :param session: An ORM session
    :param directory: A path of the directory containing the file
    :param filename: A file name
    """
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return

    secure_file_delete = models.SecureFileDelete()
    secure_file_delete.filepath = path
    session.add(secure_file_delete)


@transact
def get_file_id(session, tid, name):
    """
    Transaction returning a file ID given the file name

    :param session: An ORM session
    :param tid: A tenant on which performing the lookup
    :param name: A file name
    :return: A result model
    """
    return models.db_get(session, models.File, models.File.tid == tid, models.File.name == name).id


class FileHandler(BaseHandler):
    """
    Handler that provide public access to configuration files
    """
    check_roles = 'none'

    @inlineCallbacks
    def get(self, name):
        if name in appfiles:
            x = yield tw(db_get_file, self.request.tid, name)
            if not x and self.state.tenant_cache[self.request.tid]['mode'] != 'default':
                x = yield tw(db_get_file, 1, name)

            self.request.setHeader(b'Content-Type', appfiles[name])

            if not x and name == 'logo':
                x = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

            x = base64.b64decode(x)
            returnValue(x)
        else:
            id = yield get_file_id(self.request.tid, name)
            path = os.path.abspath(os.path.join(self.state.settings.files_path, id))
            yield self.write_file(name, path)
