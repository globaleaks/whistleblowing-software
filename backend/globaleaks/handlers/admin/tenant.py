# -*- coding: UTF-8
#
#   tenant
#   *****
# Implementation of the Tenant handlers
import base64
import os

from twisted.internet.defer import returnValue, inlineCallbacks

from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import db_update_defaults, load_appdata
from globaleaks.handlers.admin import file
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.utils.utility import log
from globaleaks.settings import Settings
from globaleaks.state import State


def serialize_tenant(store, tenant):
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


def db_create(store, desc):
    appdata = load_appdata()

    t = models.db_forge_obj(store, models.Tenant, desc)

    # required to generate/retrive the id
    store.flush()

    db_update_defaults(store, tid=t.id)

    models.config.system_cfg_init(store, tid=t.id)

    models.l10n.EnabledLanguage.add_all_supported_langs(store, t.id, appdata)

    file_descs = [
      (u'logo', 'data/logo.png'),
      (u'favicon', 'data/favicon.ico')
    ]

    for file_desc in file_descs:
        with open(os.path.join(Settings.client_path, file_desc[1]), 'r') as f:
            data = base64.b64encode(f.read())
            file.db_add_file(store, t.id, file_desc[0], u'', data)

    db_refresh_memory_variables(store)

    return t


@transact
def create(store, desc, *args, **kwargs):
    return serialize_tenant(store, db_create(store, desc, *args, **kwargs))


def db_get_tenant_list(store):
    return [serialize_tenant(store, tenant) for tenant in store.find(models.Tenant)]


@transact
def get_tenant_list(store):
    return db_get_tenant_list(store)


@transact
def get(store, id):
    return serialize_tenant(store, models.db_get(store, models.Tenant, id=id))


@transact
def update(store, id, request):
    tenant = models.db_get(store, models.Tenant, id=id)
    tenant.update(request)
    db_refresh_memory_variables(store)

    return serialize_tenant(store, tenant)


@transact
def delete(store, id):
    models.db_delete(store, models.Tenant, id=id)

    db_refresh_memory_variables(store)


class TenantCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    root_tenant_only = True
    invalidate_cache = True
    invalidate_tenant_states = True

    def get(self):
        """
        Return the list of registered tenants
        """
        if not State.tenant_cache[1].enable_multisite:
            raise errors.ForbiddenOperation

        return get_tenant_list()

    def post(self):
        """
        Create a new tenant
        """
        request = self.validate_message(self.request.content.read(), requests.AdminTenantDesc)

        if not State.tenant_cache[1].enable_multisite:
            raise errors.ForbiddenOperation

        log.info('Creating new tenant', tid=self.request.tid)

        return create(request)


class TenantInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True
    root_tenant_only = True
    invalidate_tenant_states = True

    def get(self, tenant_id):
        tenant_id = int(tenant_id)

        if not State.tenant_cache[1].enable_multisite:
            raise errors.ForbiddenOperation

        return get(tenant_id)

    def put(self, tenant_id):
        """
        Update the specified tenant.
        """
        tenant_id = int(tenant_id)

        request = self.validate_message(self.request.content.read(),
                                        requests.AdminTenantDesc)

        if not State.tenant_cache[1].enable_multisite or tenant_id == 1:
            raise errors.ForbiddenOperation

        return update(tenant_id, request)

    def delete(self, tenant_id):
        """
        Delete the specified tenant.
        """
        tenant_id = int(tenant_id)

        if not State.tenant_cache[1].enable_multisite or tenant_id == 1:
            raise errors.ForbiddenOperation

        log.info('Removing tenant with id: %d', tenant_id, tid=self.request.tid)

        return delete(tenant_id)
