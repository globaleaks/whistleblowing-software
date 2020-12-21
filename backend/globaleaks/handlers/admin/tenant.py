# -*- coding: UTF-8
import base64
import os

from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata, db_load_defaults
from globaleaks.handlers.admin import file
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import db_set_config_variable, ConfigFactory
from globaleaks.orm import db_del, db_get, transact, tw
from globaleaks.rest import requests
from globaleaks.settings import Settings
from globaleaks.utils.log import log


def serialize_tenant(session, tenant):
    ret = {
      'id': tenant.id,
      'creation_date': tenant.creation_date,
      'active': tenant.active
    }

    ret.update(ConfigFactory(session, tenant.id).serialize('tenant'))

    signup = session.query(models.Subscriber).filter(models.Subscriber.tid == tenant.id).one_or_none()
    if signup is not None:
        from globaleaks.handlers.signup import serialize_signup
        ret['signup'] = serialize_signup(signup)

    return ret


def db_initialize_tenant_submission_statuses(session, tid):
    """
    Transaction for initializing the submission statuses of a tenant

    :param session: An ORM session
    :param tid: A tenant ID
    """
    for s in [{'id': 'new', 'label': {'en': 'New'}},
              {'id': 'opened', 'label': {'en': 'Opened'}},
              {'id': 'closed', 'label': {'en': 'Closed'}}]:
        state = models.SubmissionStatus()
        state.id = s['id']
        state.tid = tid
        state.label = s['label']
        session.add(state)


def db_create(session, desc):
    t = models.Tenant()

    session.add(t)

    # required to generate the tenant id
    session.flush()

    appdata = load_appdata()

    if t.id == 1:
        db_load_defaults(session)

    models.config.initialize_config(session, t.id, desc['mode'])

    for var in ['mode', 'name', 'subdomain']:
        db_set_config_variable(session, t.id, var, desc[var])

    models.config.add_new_lang(session, t.id, 'en', appdata)

    db_initialize_tenant_submission_statuses(session, t.id)

    if desc['mode'] == 'default':
        file_descs = [
            ('favicon', 'data/favicon.ico')
        ]

        for file_desc in file_descs:
            with open(os.path.join(Settings.client_path, file_desc[1]), 'rb') as f:
                data = base64.b64encode(f.read()).decode()
                file.db_add_file(session, t.id, file_desc[0], '', data)

    db_refresh_memory_variables(session, [t.id])

    return t


@transact
def create(session, desc, *args, **kwargs):
    return serialize_tenant(session, db_create(session, desc, *args, **kwargs))


def db_get_tenant_list(session):
    return [serialize_tenant(session, t) for t in session.query(models.Tenant)]


@transact
def get_tenant_list(session):
    return db_get_tenant_list(session)


@transact
def get(session, tid):
    return serialize_tenant(session, db_get(session, models.Tenant, models.Tenant.id == tid))


@transact
def update(session, tid, request):
    tenant = db_get(session, models.Tenant, models.Tenant.id == tid)

    tenant.active = request['active']

    for var in ['mode', 'name', 'subdomain']:
        db_set_config_variable(session, tid, var, request[var])

    return serialize_tenant(session, tenant)


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
    root_tenant_only = True
    invalidate_cache = True
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

        return tw(db_del, models.Tenant, models.Tenant.id == tenant_id)
