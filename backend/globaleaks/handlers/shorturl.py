# -*- coding: utf-8
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from twisted.internet.defer import inlineCallbacks


@transact
def translate_shorturl(store, shorturl):
    shorturl = store.find(models.ShortURL, shorturl=shorturl).one()
    if not shorturl:
        return '/'

    return shorturl.longurl


class ShortUrlInstance(BaseHandler):
    """
    This handler implement the platform url shortener
    """
    check_roles = '*'

    @inlineCallbacks
    def get(self, shorturl):
        longurl = yield translate_shorturl(shorturl)
        self.redirect(longurl)
