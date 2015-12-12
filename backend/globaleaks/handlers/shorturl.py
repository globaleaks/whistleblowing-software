from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact_ro

@transact_ro
def translate_shorturl(store, shorturl):
    shorturl = store.find(models.ShortURL, models.ShortURL.shorturl == shorturl).one()
    if not shorturl:
        return '/'

    return shorturl.longurl


class ShortUrlInstance(BaseHandler):
    """
    This handler implement the platform url shortener
    """
    handler_exec_time_threshold = 30

    @transport_security_check('unauth')
    @unauthenticated
    @inlineCallbacks
    def get(self, shorturl):
        longurl = yield translate_shorturl(shorturl)
        self.redirect(longurl)
