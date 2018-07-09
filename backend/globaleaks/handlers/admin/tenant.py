
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


def initialize_submission_statuses(session, tid):
    for s in [{'label': {'en': 'New'}, 'system_usage': 'new'},
              {'label': {'en': 'Open'}, 'system_usage':'open'},
              {'label': {'en':' Closed'}, 'system_usage': 'closed'}]:
        state = models.SubmissionStatus()
        state.tid = tid
        state.label = s['label']
        state.system_defined = True
        state.system_usage = s['system_usage']
        session.add(state)


def serialize_tenant(session, tenant, signup=None):
    from globaleaks.handlers.signup import serialize_signup

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

    if signup is not None:
        ret['signup'] = serialize_signup(signup)

    return ret


def db_preallocate(session, desc):
    t = models.db_forge_obj(session, models.Tenant, desc)

    # required to generate the tenant id
    session.flush()

    return t


def db_initialize(session, tid):
    appdata = load_appdata()

    models.config.system_cfg_init(session, tid=tid)

    models.config.add_new_lang(session, tid, u'en', appdata)

    initialize_submission_statuses(session, tid)

    file_descs = [
      (u'logo', 'data/logo.png'),
      (u'favicon', 'data/favicon.ico')
    ]

    for file_desc in file_descs:
        with open(os.path.join(Settings.client_path, file_desc[1]), 'rb') as f:
            data = base64.b64encode(f.read())
            file.db_add_file(session, tid, file_desc[0], u'', data)


def db_create(session, desc):
    t = db_preallocate(session, desc)

    t.active = True

    db_initialize(session, t.id)

    db_refresh_memory_variables(session, [t.id])

    return t


@transact
def create(session, desc, *args, **kwargs):
    return serialize_tenant(session, db_create(session, desc, *args, **kwargs))


def db_get_tenant_list(session):
    return [serialize_tenant(session, r[0], r[1]) for r in session.query(models.Tenant, models.Signup)
                                                                  .outerjoin(models.Signup, models.Tenant.id == models.Signup.tid)]


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

    # A tenant created via signup but not activate may require initialization
    if not session.query(models.Config).filter(models.Config.tid == id).count():
        db_initialize(session, id)

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
    invalidate_tenant_state = True

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
    invalidate_tenant_state = True

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
