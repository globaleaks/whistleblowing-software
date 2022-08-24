# -*- coding: utf-8 -*-
#
# Handler exposing application files
import os

from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import errors
from globaleaks.utils.fs import directory_traversal_check


class StaticFileHandler(BaseHandler):
    check_roles = 'any'
    allowed_mimetypes = [
        'font/ttf',
        'font/woff',
        'font/woff2',
        'image/png',
        'text/css',
        'text/html',
        'text/javascript'
    ]

    def __init__(self, state, request):
        BaseHandler.__init__(self, state, request)

        self.root = "%s%s" % (os.path.abspath(state.settings.client_path), "/")

    def get(self, filename):
        if not filename:
            filename = 'index.html'

        abspath = os.path.abspath(os.path.join(self.root, filename))
        directory_traversal_check(self.root, abspath)

        return self.write_file(filename, abspath)
