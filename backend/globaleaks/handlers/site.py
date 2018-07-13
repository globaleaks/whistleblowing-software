
# -*- coding: UTF-8
#
#   tenant
#   *****
# Implementation of the Tenant handlers
import base64
import os

from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.admin import file
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.utility import log
from globaleaks.settings import Settings
from globaleaks.state import State


def serialize_site(session, tenant, signup=None):
    ret = {
        'id': tenant.id,
        'label': tenant.label,
        'active': tenant.active,
        'subdomain': tenant.subdomain,
        'hostname': '',
        'onionservice': ''
    }

    if tenant.id in State.tenant_cache:
        tc = State.tenant_cache[tenant.id]
        ret['hostname'] = tc.hostname
        ret['onionservice'] = tc.onionservice

    return ret


def db_get_site_list(session):
    return [serialize_site(session, t) for t in session.query(models.Tenant).filter(models.Tenant.active == True)]


@transact
def get_site_list(session):
    return db_get_site_list(session)


class SiteCollection(BaseHandler):
    check_roles = '*'
    cache_resource = True
    root_tenant_only = True

    def get(self):
        """
        Return the list of registered tenants
        """
        if 1 not in self.state.tenant_cache or \
           not self.state.tenant_cache[1].enable_signup or \
           self.state.tenant_cache[1].signup_mode != u'whistleblowing.it':
           return []

        return get_site_list()
