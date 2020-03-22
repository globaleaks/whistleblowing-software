# -*- coding: utf-8
from globaleaks import __version__
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils.fs import read_file


class ManifestHandler(BaseHandler):
    check_roles = 'user'

    def get(self):
        """
        Get the applicatin manifest
        """
        return {
            'changelog': read_file('/usr/share/globaleaks/LICENSE'),
            'license': read_file('/usr/share/globaleaks/CHANGELOG'),
            'version': __version__
        }
