# -*- coding: utf-8
#
#   redirect
#   *****
# Implementation of the URL redirect handlers
#
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests


def serialize_redirect(redirect):
    return {
        'id': redirect.id,
        'path1': redirect.path1,
        'path2': redirect.path2
    }


@transact
def get_redirect_list(session, tid):
    return [serialize_redirect(redirect) for redirect in session.query(models.Redirect).filter(models.Redirect.tid == tid)]


@transact
def create(session, tid, request):
    request['tid'] = tid
    redirect = models.db_forge_obj(session, models.Redirect, request)
    return serialize_redirect(redirect)


class RedirectCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return the list of registered redirects
        """
        return get_redirect_list(self.request.tid)

    def post(self):
        """
        Create a new redirect
        """
        request = self.validate_message(self.request.content.read(), requests.AdminRedirectDesc)

        return create(self.request.tid, request)


class RedirectInstance(BaseHandler):
    check_roles = 'admin'

    def delete(self, redirect_id):
        """
        Delete the specified redirect.
        """
        return models.delete(models.Redirect, models.Redirect.tid == self.request.tid, models.Redirect.id == redirect_id)
