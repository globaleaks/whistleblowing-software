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
def get(store, lang):
    texts = store.find(models.CustomTexts, lang=lang).one()
    return texts.texts if texts is not None else {}


@transact
def update(store, lang, request):
    texts = store.find(models.CustomTexts, lang=lang).one()
    if texts is None:
        store.add(models.CustomTexts({'lang': lang, 'texts': request}))
    else:
        texts.texts = request


class AdminL10NHandler(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def get(self, lang):
        return get(lang)

    def put(self, lang):
        return update(lang, json.loads(self.request.content.read()))

    def delete(self, lang):
        return models.delete(models.CustomTexts, lang=lang)
