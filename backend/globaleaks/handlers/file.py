# -*- coding: utf-8 -*-
#
# Handlers exposing customization files
import base64
import os
import re

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.file import get_file_id_by_name, special_files
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest.requests import uuid_regexp

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
    def get(self, id):
        if id in appfiles:
            self.request.setHeader(b'Content-Type', appfiles[id])

        if not re.match(uuid_regexp, id):
            id = yield get_file_id_by_name(self.request.tid, id)

        path = os.path.abspath(os.path.join(self.state.settings.files_path, id))
        yield self.write_file(path, path)
