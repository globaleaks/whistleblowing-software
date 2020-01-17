# -*- coding: utf-8 -*-
#
# Handlers dealing with download of texts translations and customizations
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
    """
    Functio that returns the json filepath given a language
    :param lang: Language
    :return: A file path of the json file containing the specified language
    """
    return os.path.abspath(os.path.join(Settings.client_path, 'l10n', '%s.json' % lang))


@transact
def get_l10n(session, tid, lang):
    """
    Transaction for retrieving the custom texts configured for a specific language
    :param session: An ORM session
    :param tid:  The tenant ID of the tenant on which perform the lookup
    :param lang: A requested language
    :return: A dictionary containing the custom texts configured for a specific language
    """
    if tid != 1:
        config = ConfigFactory(session, 1)

        if config.get_val('mode') != 'default':
            tid = 1

    path = langfile_path(lang)
    directory_traversal_check(Settings.client_path, path)

    if not os.path.exists(path):
        raise errors.ResourceNotFound()

    custom_texts = session.query(models.CustomTexts).filter(models.CustomTexts.lang == lang, models.CustomTexts.tid == tid).one_or_none()
    custom_texts = custom_texts.texts if custom_texts is not None else {}

    texts = read_json_file(path).update(custom_texts)

    return texts


class L10NHandler(BaseHandler):
    check_roles = 'none'
    cache_resource = True

    def get(self, lang):
        return get_l10n(self.request.tid, lang)
