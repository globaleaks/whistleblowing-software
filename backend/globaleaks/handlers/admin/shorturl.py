# -*- coding: UTF-8
#
#   shorturl
#   *****
# Implementation of the URL shortener handlers
#
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
    return [serialize_shorturl(shorturl) for shorturl in store.find(models.ShortURL)]


@transact
def create_shorturl(store, request):
    shorturl = models.db_forge_obj(store, models.ShortURL, request)
    return serialize_shorturl(shorturl)


class ShortURLCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return the list of registered short urls
        """
        return get_shorturl_list()

    def post(self):
        """
        Create a new shorturl
        """
        request = self.validate_message(self.request.content.read(), requests.AdminShortURLDesc)

        return create_shorturl(request)


class ShortURLInstance(BaseHandler):
    check_roles = 'admin'

    def delete(self, shorturl_id):
        """
        Delete the specified shorturl.
        """
        return models.delete(models.ShortURL, id=shorturl_id)
