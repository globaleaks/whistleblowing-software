# -*- coding: UTF-8
#
#   shorturl
#   *****
# Implementation of the URL shortener handlers
#
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests, errors


def serialize_shorturl(shorturl):
    return {
        'id': shorturl.id,
        'shorturl': shorturl.shorturl,
        'longurl': shorturl.longurl
    }


@transact
def get_shorturl_list(store):
    shorturls = store.find(models.ShortURL)
    return [serialize_shorturl(shorturl) for shorturl in shorturls]


@transact
def create_shorturl(store, request):
    shorturl = models.ShortURL(request)
    store.add(shorturl)
    return serialize_shorturl(shorturl)


@transact
def delete_shorturl(store, shorturl_id):
    shorturl = store.find(models.ShortURL, models.ShortURL.id == shorturl_id).one()
    if not shorturl:
        raise errors.ShortURLIdNotFound

    store.remove(shorturl)



class ShortURLCollection(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return the list of registered short urls
        """
        response = yield get_shorturl_list()

        self.write(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new shorturl
        """
        request = self.validate_message(self.request.body, requests.AdminShortURLDesc)

        response = yield create_shorturl(request)

        self.set_status(201) # Created
        self.write(response)


class ShortURLInstance(BaseHandler):
    @inlineCallbacks
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self, shorturl_id):
        """
        Delete the specified shorturl.
        """
        yield delete_shorturl(shorturl_id)
