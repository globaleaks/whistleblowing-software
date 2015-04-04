# -*- coding: utf-8 -*-
#
# langfiles
#  **************
#

from __future__ import with_statement
import os

from globaleaks.settings import GLSetting
from globaleaks.handlers.base import BaseStaticFileHandler
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.security import directory_traversal_check


class LanguageFileHandler(BaseStaticFileHandler):
    """
    This class is used to return the custom translation files;
    if the file are not present, default translations are returned
    """

    def langfile_path(self, lang):
        return os.path.abspath(os.path.join(GLSetting.glclient_path, 'l10n', '%s.json' % lang))

    def custom_langfile_path(self, lang):
        return os.path.abspath(os.path.join(GLSetting.static_path_l10n, '%s.json' % lang))

    @transport_security_check('unauth')
    @unauthenticated
    def get(self, lang):
        self.set_header('Content-Type', 'application/json')

        path = self.custom_langfile_path(lang)
        directory_traversal_check(GLSetting.static_path_l10n, path)
        self.root = GLSetting.static_path_l10n

        if not os.path.exists(path):
            path = self.langfile_path(lang)
            directory_traversal_check(GLSetting.glclient_path, path)
            self.root = os.path.abspath(os.path.join(GLSetting.glclient_path, 'l10n'))

        BaseStaticFileHandler.get(self, path)
