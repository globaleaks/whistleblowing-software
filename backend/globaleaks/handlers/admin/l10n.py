# -*- coding: utf-8 -*-
#
# admin/lang
#  **************
#
# Backend supports for jQuery File Uploader, and implementation of the
# file language statically uploaded by the Admin

# This code differs from handlers/file.py because files here are not tracked in the DB
import json

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact


@transact
def get_custom_texts(store, lang):
    texts = store.find(models.CustomTexts, models.CustomTexts.lang == unicode(lang)).one()
    return texts.texts if texts is not None else {}


@transact
def update_custom_texts(store, lang, texts):
    custom_texts = store.find(models.CustomTexts, models.CustomTexts.lang == unicode(lang)).one()
    if custom_texts is None:
        custom_texts = models.CustomTexts()
        custom_texts.lang = lang
        store.add(custom_texts)

    custom_texts.texts = texts


@transact
def delete_custom_texts(store, lang):
    custom_texts = store.find(models.CustomTexts, models.CustomTexts.lang == unicode(lang)).one()
    if custom_texts is not None:
        store.remove(custom_texts)


class AdminL10NHandler(BaseHandler):
    check_roles = 'admin'

    def get(self, lang):
        return get_custom_texts(lang)

    def put(self, lang):
        request = json.loads(self.request.content.read())

        return update_custom_texts(lang, request)

    def delete(self, lang):
        return delete_custom_texts(lang)
