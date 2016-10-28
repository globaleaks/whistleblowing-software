# -*- coding: utf-8 -*-
#
# langfiles
#  **************
#
import json
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.security import directory_traversal_check


def langfile_path(lang):
    return os.path.abspath(os.path.join(GLSettings.client_path, 'l10n', '%s.json' % lang))


@transact
def get_l10n(store, lang):
    path = langfile_path(lang)
    directory_traversal_check(GLSettings.client_path, path)

    with open(path, 'rb') as f:
        texts = json.loads(f.read())

    custom_texts = store.find(models.CustomTexts, models.CustomTexts.lang == unicode(lang)).one()
    custom_texts = custom_texts.texts if custom_texts is not None else {}

    texts.update(custom_texts)

    return texts


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

        l10n = yield GLApiCache.get('l10n', self.request.language,
                                    get_l10n, self.request.language)

        self.write(l10n)
