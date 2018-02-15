# -*- coding: UTF-8
# Implementation of the Admin Signup handlers

from globaleaks import models
from globaleaks.handlers.signup import serialize_signup
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact


@transact
def get_signup_list(session):
    return [serialize_signup(s) for s in session.query(models.Signup)]


class SignupList(BaseHandler):
    check_roles = 'admin'
    root_tenant_only = True

    def get(self):
        """
        Return the list of registered tenants
        """
        return get_signup_list()
