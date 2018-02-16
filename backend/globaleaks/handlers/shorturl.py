# -*- coding: utf-8 -*-
#
# Handlers implementing the url shortener redirect
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import errors


@transact
def translate_shorturl(session, tid, shorturl):
    shorturl = session.query(models.ShortURL).filter(models.ShortURL.shorturl == shorturl, models.ShortURL.tid == tid).one_or_none()
    if shorturl is None:
        raise errors.ResourceNotFound()

    return shorturl.longurl


class ShortURL(BaseHandler):
    """
    This handler implement the platform url shortener
    """
    check_roles = '*'

    @inlineCallbacks
    def get(self, shorturl):
        longurl = yield translate_shorturl(self.request.tid, shorturl)
        self.redirect(longurl)
