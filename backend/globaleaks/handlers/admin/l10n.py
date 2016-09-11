# -*- coding: utf-8 -*-
#
# admin/lang
#  **************
#
# Backend supports for jQuery File Uploader, and implementation of the
# file language statically uploaded by the Admin

# This code differs from handlers/file.py because files here are not tracked in the DB

from __future__ import with_statement

import json
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact, transact_ro
from globaleaks.rest.apicache import GLApiCache


@transact_ro
def get_custom_texts(store, lang):
    texts = store.find(models.CustomTexts, models.CustomTexts.lang == lang).one()
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
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self, lang):
        custom_texts = yield get_custom_texts(lang)

        self.write(custom_texts)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self, lang):
        request = json.loads(self.request.body)

        yield update_custom_texts(lang, request)

        GLApiCache.invalidate()

        self.set_status(202)  # Updated

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, lang):
        yield delete_custom_texts(lang)

        GLApiCache.invalidate()
