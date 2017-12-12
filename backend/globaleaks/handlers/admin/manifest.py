# -*- coding: utf-8
import os

from globaleaks import __version__
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils.utility import read_file


class ManifestHandler(BaseHandler):
    check_roles = 'admin'

    def get(self):
        """
        Get the applicatin manifest
        """
        LICENSE = '/usr/share/globaleaks/LICENSE'
        if os.path.exists(LICENSE):
            LICENSE = read_file(LICENSE)

        CHANGELOG = '/usr/share/globaleaks/CHANGELOG'
        if os.path.exists(CHANGELOG):
            CHANGELOG = read_file(CHANGELOG)

        return {
            'changelog': CHANGELOG,
            'license': LICENSE,
            'version': __version__
        }
