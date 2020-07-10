# -*- coding: UTF-8
import base64
import os

from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.admin import file
from globaleaks.handlers.admin.submission_statuses import db_initialize_tenant_submission_statuses
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import db_set_config_variable
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.settings import Settings
from globaleaks.state import State
from globaleaks.utils.log import log


def serialize_tenant(session, tenant, signup=None):
    from globaleaks.handlers.signup import serialize_signup

    ret = {
        'id': tenant.id,
        'label': tenant.label,
        'active': tenant.active,
        'subdomain': tenant.subdomain,
        'hostname': '',
        'onionservice': '',
        'mode': '',
        'creation_date': tenant.creation_date
    }

    if tenant.id in State.tenant_cache:
        tc = State.tenant_cache[tenant.id]
        ret['hostname'] = tc.hostname
        ret['onionservice'] = tc.onionservice
        ret['mode'] = tc.mode

    if signup is not None:
        ret['signup'] = serialize_signup(signup)

    return ret


def db_preallocate_tenant(session, desc):
    t = models.db_forge_obj(session, models.Tenant, desc)

    # required to generate the tenant id
    session.flush()

    return t


def db_initialize_tenant(session, tenant, mode):
    tenant.active = True

    appdata = load_appdata()

    models.config.initialize_config(session, tenant.id, mode)

    models.config.add_new_lang(session, tenant.id, 'en', appdata)

    db_initialize_tenant_submission_statuses(session, tenant.id)

    if mode == 'default':
        file_descs = [
            ('favicon', 'data/favicon.ico')
        ]

        for file_desc in file_descs:
            with open(os.path.join(Settings.client_path, file_desc[1]), 'rb') as f:
                data = base64.b64encode(f.read()).decode()
                file.db_add_file(session, tenant.id, file_desc[0], '', data)


def db_create(session, desc):
    t = db_preallocate_tenant(session, desc)

    db_initialize_tenant(session, t, desc['mode'])

    db_refresh_memory_variables(session, [t.id])

    return t


@transact
def create(session, desc, *args, **kwargs):
    return serialize_tenant(session, db_create(session, desc, *args, **kwargs))


def db_get_tenant_list(session):
    return [serialize_tenant(session, r[0], r[1]) for r in session.query(models.Tenant, models.Signup)
                                                                  .outerjoin(models.Signup, models.Signup.tid == models.Tenant.id)]


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

    # A tenant created via signup but not activated may require initialization
    if not session.query(models.Config).filter(models.Config.tid == id).count():
        db_initialize_tenant(session, tenant, request['mode'])
    else:
        db_set_config_variable(session, id, 'mode', request['mode'])

    db_refresh_memory_variables(session, [id])

    return serialize_tenant(session, tenant)


@transact
def delete(session, id):
    models.db_delete(session, models.Tenant, models.Tenant.id == id)

    db_refresh_memory_variables(session, [id])


class TenantCollection(BaseHandler):
    check_roles = 'admin'
    root_tenant_only = True
    invalidate_cache = True
    refresh_connection_endpoints = True

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
    refresh_connection_endpoints = True

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
