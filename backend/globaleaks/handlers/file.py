# -*- coding: utf-8 -*-
#
# Handlers exposing customization files
import base64
import os

from six import text_type
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.admin.file import get_file
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact

appfiles = {
    'favicon': 'image-x-icon',
    'css': 'text/css',
    'logo': 'image/png',
    'script': 'application/javascript'
}


def db_mark_file_for_secure_deletion(session, directory, filename):
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return

    secure_file_delete = models.SecureFileDelete()
    secure_file_delete.filepath = path
    session.add(secure_file_delete)


@transact
def get_file_id(session, tid, name):
    return models.db_get(session, models.File, models.File.tid == tid, models.File.name == text_type(name)).id


class FileHandler(BaseHandler):
    check_roles = 'none'

    @inlineCallbacks
    def get(self, name):
        if name in appfiles:
            file_tid = self.request.tid
            if self.state.tenant_cache[self.request.tid]['mode'] != u'default' and name in ['css', 'script']:
                file_tid = 1

            self.request.setHeader(b'Content-Type', appfiles[name])
            x = yield get_file(file_tid, name)
            x = base64.b64decode(x)
            returnValue(x)
        else:
            id = yield get_file_id(self.request.tid, name)
            path = os.path.abspath(os.path.join(self.state.settings.files_path, id))
            yield self.write_file(name, path)


class AppFileHandler(BaseHandler):
    check_roles = 'none'

    @inlineCallbacks
    def get(self, name):
        if name not in appfiles:
            return

        file_tid = self.request.tid
        if self.state.tenant_cache[self.request.tid]['mode'] != u'default' and name in ['css', 'script']:
            file_tid = 1

        self.request.setHeader(b'Content-Type', appfiles[name])
        x = yield get_file(file_tid, name)
        returnValue(base64.b64decode(x))
