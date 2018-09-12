# -*- coding: utf-8 -*-
#
# Handlers dealing with download of texts translations and customiations
import os

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.utils.fs import directory_traversal_check
from globaleaks.utils.utility import read_json_file


def langfile_path(lang):
    return os.path.abspath(os.path.join(Settings.client_path, 'l10n', '%s.json' % lang))


@transact
def get_l10n(session, tid, lang):
    if tid != 1:
        node = ConfigFactory(session, 1, 'public_node')

        if node.get_val(u'mode') == u'whistleblowing.it':
            tid = 1

    path = langfile_path(lang)
    directory_traversal_check(Settings.client_path, path)

    if not os.path.exists(path):
        raise errors.ResourceNotFound()

    texts = read_json_file(path)

    custom_texts = session.query(models.CustomTexts).filter(models.CustomTexts.lang == lang, models.CustomTexts.tid == tid).one_or_none()
    custom_texts = custom_texts.texts if custom_texts is not None else {}

    texts.update(custom_texts)

    return texts


class L10NHandler(BaseHandler):
    check_roles = '*'
    cache_resource = True

    def get(self, lang):
        return get_l10n(self.request.tid, lang)
