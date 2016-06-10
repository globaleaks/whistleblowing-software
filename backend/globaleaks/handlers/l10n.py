# -*- coding: utf-8 -*-
#
# langfiles
#  **************
#

from __future__ import with_statement
import json
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.settings import GLSettings
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin import l10n as admin_l10n
from globaleaks.security import directory_traversal_check


def langfile_path(lang):
    return os.path.abspath(os.path.join(GLSettings.client_path, 'l10n', '%s.json' % lang))


class L10NHandler(BaseHandler):
    """
    This class is used to return the custom translation files;
    if the file are not present, default translations are returned
    """
    @BaseHandler.transport_security_check('unauth')
    @BaseHandler.unauthenticated
    @inlineCallbacks
    def get(self, lang):
        self.set_header('Content-Type', 'application/json')

        path = langfile_path(lang)
        directory_traversal_check(GLSettings.client_path, path)
        self.root = os.path.abspath(os.path.join(GLSettings.client_path, 'l10n'))

        with open(path, 'rb') as f:
            texts = json.loads(f.read())

        custom_texts = yield admin_l10n.get_custom_texts(lang)

        texts.update(custom_texts)
        self.write(texts)
