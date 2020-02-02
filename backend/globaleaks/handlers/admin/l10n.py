# -*- coding: utf-8 -*-
import json

from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import can_edit_general_settings_or_raise
from globaleaks.orm import transact


@transact
def get(session, tid, lang):
    """
    Transaction for retrieving the texts customization of a tenant

    :param session: An ORM session
    :param tid: A tenant ID
    :param lang: The language to be used for the lookup
    :return: The sequence of customizations
    """
    texts = session.query(models.CustomTexts).filter(models.CustomTexts.tid == tid,
                                                     models.CustomTexts.lang == lang).one_or_none()
    return texts.texts if texts is not None else {}


@transact
def update(session, tid, lang, request):
    """
    Transaction for updating the texts customizations of a tenant

    :param session: An ORM session
    :param tid: A tentant ID
    :param lang: The language to be used for the update
    :param request: The customization data
    """
    session.merge(models.CustomTexts({'tid': tid, 'lang': lang, 'texts': request}))


class AdminL10NHandler(BaseHandler):
    check_roles = 'user'
    invalidate_cache = True

    @inlineCallbacks
    def get(self, lang):
        yield can_edit_general_settings_or_raise(self)
        result = yield get(self.request.tid, lang)
        returnValue(result)

    @inlineCallbacks
    def put(self, lang):
        yield can_edit_general_settings_or_raise(self)
        result = yield update(self.request.tid, lang, json.loads(self.request.content.read()))
        returnValue(result)

    @inlineCallbacks
    def delete(self, lang):
        yield can_edit_general_settings_or_raise(self)
        result = yield models.delete(models.CustomTexts, models.CustomTexts.tid == self.request.tid, models.CustomTexts.lang == lang)
        returnValue(result)
