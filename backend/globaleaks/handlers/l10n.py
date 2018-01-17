# -*- coding: utf-8 -*-
#
# langfiles
#  **************
#
import os

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.security import directory_traversal_check
from globaleaks.settings import Settings
from globaleaks.utils.utility import read_json_file


def langfile_path(lang):
    return os.path.abspath(os.path.join(Settings.client_path, 'l10n', '%s.json' % lang))


@transact
def get_l10n(session, tid, lang):
    path = langfile_path(lang)
    directory_traversal_check(Settings.client_path, path)

    texts = read_json_file(path)

    custom_texts = session.query(models.CustomTexts).filter(models.CustomTexts.lang == lang, models.CustomTexts.tid == tid).one_or_none()
    custom_texts = custom_texts.texts if custom_texts is not None else {}

    texts.update(custom_texts)

    return texts


class L10NHandler(BaseHandler):
    """
    This class is used to return the custom translation files;
    if the file are not present, default translations are returned
    """
    check_roles = '*'
    cache_resource = True

    def get(self, lang):
        return get_l10n(self.request.tid, lang)
