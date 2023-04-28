# -*- coding: utf-8 -*-
#
# Handlers exposing custom script files
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import serve_file, BaseHandler
from globaleaks.utils.fs import directory_traversal_check


class ScriptHandler(BaseHandler):
    """
    Handler that provide access to custom script files
    """
    check_roles = 'any'

    allowed_mimetypes = [
      'text/javascript'
    ]

    def get(self):
        path1 = os.path.abspath(os.path.join(self.state.settings.scripts_path, str(self.request.tid)))
        path2 = os.path.abspath(os.path.join(self.state.settings.scripts_path, "1"))

        if os.path.exists(path1):
            path = path1
        elif self.request.tid != 1 and \
                self.request.tid in self.state.tenants and \
                self.state.tenants[self.request.tid].cache.mode not in ['default', 'demo'] and \
                os.path.exists(path2):
            path = path2
        else:
            self.request.setHeader(b'Content-Type', "text/javascript")
            return ""

        directory_traversal_check(self.state.settings.scripts_path, path)

        return self.write_file('script.js', path)
