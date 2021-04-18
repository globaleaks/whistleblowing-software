# -*- coding: utf-8 -*-
#
# Handlers exposing customization files
import base64
import os
import urllib

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.file import get_file_id_by_name, special_files
from globaleaks.handlers.base import BaseHandler

appfiles = {
    'favicon': 'image/x-icon',
    'logo': 'image/png',
    'css': 'text/css',
    'script': 'application/javascript'
}

class FileHandler(BaseHandler):
    """
    Handler that provide public access to configuration files
    """
    check_roles = 'any'

    @inlineCallbacks
    def get(self, name):
        name = urllib.parse.unquote(name)
        if name in appfiles:
            self.request.setHeader(b'Content-Type', appfiles[name])
        else:
            self.request.setHeader(b'Content-Type', 'application/octet-stream')

        id = yield get_file_id_by_name(self.request.tid, name)
        if not id:
            id = yield get_file_id_by_name(1, name)

        path = os.path.abspath(os.path.join(self.state.settings.files_path, id))
        yield self.write_file(path, path)
