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
        path = os.path.abspath(os.path.join(self.state.settings.scripts_path, str(self.request.tid)))
        if not os.path.exists(path):
            path = os.path.abspath(os.path.join(self.state.settings.scripts_path, "1"))

        directory_traversal_check(self.state.settings.scripts_path, path)

        return self.write_file('script.js', path)
