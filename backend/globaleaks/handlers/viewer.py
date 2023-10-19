
# -*- coding: utf-8 -*-
#
# Handler exposing viewer application
import os

from globaleaks.handlers.staticfile import StaticFileHandler
from globaleaks.utils.fs import directory_traversal_check


class ViewerHandler(StaticFileHandler):
    def get(self, filename):
        abspath = os.path.abspath(os.path.join(self.root, filename))
        directory_traversal_check(self.root, abspath)

        self.request.setHeader(b'Access-Control-Allow-Origin', "null")
        if filename == 'viewer/index.html':
            self.request.setHeader(b'Content-Security-Policy',
                                   b"base-uri 'none';"
                                   b"default-src 'none';"
                                   b"connect-src blob:;"
                                   b"form-action 'none';"
                                   b"frame-ancestors 'self';"
                                   b"img-src blob:;"
                                   b"media-src blob:;"
                                   b"script-src 'self';"
                                   b"style-src 'self';")

            self.request.setHeader(b"Cross-Origin-Resource-Policy", "cross-origin")

        return self.write_file(filename, abspath)
