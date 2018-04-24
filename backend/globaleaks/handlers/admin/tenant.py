
# -*- coding: UTF-8
#
#   tenant
#   *****
# Implementation of the Tenant handlers
import base64
import os

from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import db_update_defaults, load_appdata
from globaleaks.handlers.admin import file
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.utility import log
from globaleaks.settings import Settings
from globaleaks.state import State


def serialize_tenant(session, tenant):
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


def db_create(session, desc):
    appdata = load_appdata()

    t = models.db_forge_obj(session, models.Tenant, desc)

    # required to generate/retrive the id
    session.flush()

    db_update_defaults(session)

    models.config.system_cfg_init(session, tid=t.id)

    models.config.add_new_lang(session, t.id, u'en', appdata)

    file_descs = [
      (u'logo', 'data/logo.png'),
      (u'favicon', 'data/favicon.ico')
    ]

    for file_desc in file_descs:
        with open(os.path.join(Settings.client_path, file_desc[1]), 'rb') as f:
            data = base64.b64encode(f.read())
            file.db_add_file(session, t.id, file_desc[0], u'', data)

    db_refresh_memory_variables(session, [t.id])

    return t


@transact
def create(session, desc, *args, **kwargs):
    return serialize_tenant(session, db_create(session, desc, *args, **kwargs))


def db_get_tenant_list(session):
    return [serialize_tenant(session, tenant) for tenant in session.query(models.Tenant)]


@transact
def get_tenant_list(session):
    return db_get_tenant_list(session)


@transact
def get(session, id):
    return serialize_tenant(session, models.db_get(session, models.Tenant, models.Tenant.id == id))


@transact
def update(session, id, request):
    tenant = models.db_get(session, models.Tenant, models.Tenant.id == id)
    tenant.update(request)
    db_refresh_memory_variables(session, [id])

    return serialize_tenant(session, tenant)


@transact
def delete(session, id):
    models.db_delete(session, models.Tenant, models.Tenant.id == id)

    db_refresh_memory_variables(session, [id])


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
        return get_tenant_list()

    def post(self):
        """
        Create a new tenant
        """
        request = self.validate_message(self.request.content.read(), requests.AdminTenantDesc)

        log.info('Creating new tenant', tid=self.request.tid)

        return create(request)


class TenantInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True
    root_tenant_only = True
    invalidate_tenant_states = True

    def get(self, tenant_id):
        tenant_id = int(tenant_id)

        return get(tenant_id)

    def put(self, tenant_id):
        """
        Update the specified tenant.
        """
        tenant_id = int(tenant_id)

        request = self.validate_message(self.request.content.read(),
                                        requests.AdminTenantDesc)

        return update(tenant_id, request)

    def delete(self, tenant_id):
        """
        Delete the specified tenant.
        """
        tenant_id = int(tenant_id)

        log.info('Removing tenant with id: %d', tenant_id, tid=self.request.tid)

        return delete(tenant_id)
