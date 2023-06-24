# -*- coding: UTF-8
from globaleaks import models
from globaleaks.db.appdata import load_appdata, db_load_defaults
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.wizard import db_wizard
from globaleaks.models import serializers
from globaleaks.models.config import db_set_config_variable
from globaleaks.orm import db_del, db_get, transact, tw
from globaleaks.rest import requests
from globaleaks.utils.tls import gen_selfsigned_certificate


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

    t.active = desc['active']

    session.add(t)

    # required to generate the tenant id
    session.flush()

    appdata = load_appdata()

    if t.id == 1:
        db_load_defaults(session)

    models.config.initialize_config(session, t.id, desc['mode'])

    if t.id == 1:
        key, cert = gen_selfsigned_certificate()
        db_set_config_variable(session, 1, 'https_selfsigned_key', key)
        db_set_config_variable(session, 1, 'https_selfsigned_cert', cert)

    for var in ['mode', 'name', 'subdomain']:
        db_set_config_variable(session, t.id, var, desc[var])

    models.config.add_new_lang(session, t.id, 'en', appdata)

    db_initialize_tenant_submission_statuses(session, t.id)

    return t


@transact
def create(session, desc, *args, **kwargs):
    t = db_create(session, desc, *args, **kwargs)

    return serializers.serialize_tenant(session, t)


@transact
def create_and_initialize(session, desc, *args, **kwargs):
    t = db_create(session, desc, *args, **kwargs)

    wizard = {
        'node_language': 'en',
        'node_name': desc['name'],
        'profile': 'default',
        'skip_admin_account_creation': True,
        'skip_recipient_account_creation': True,
        'enable_developers_exception_notification': True
    }

    db_wizard(session, t.id, '', wizard)

    return serializers.serialize_tenant(session, t)


def db_get_tenant_list(session):
    ret = []

    for t, s in session.query(models.Tenant, models.Subscriber).join(models.Subscriber, models.Subscriber.tid == models.Tenant.id, isouter=True):
        ret.append(serializers.serialize_tenant(session, t))

        if s:
            ret[-1]['signup'] = serializers.serialize_signup(s)

    return ret


@transact
def get_tenant_list(session):
    return db_get_tenant_list(session)


@transact
def get(session, tid):
    return serializers.serialize_tenant(session, db_get(session, models.Tenant, models.Tenant.id == tid))


@transact
def update(session, tid, request):
    t = db_get(session, models.Tenant, models.Tenant.id == tid)

    t.active = request['active']

    for var in ['mode', 'name', 'subdomain']:
        db_set_config_variable(session, tid, var, request[var])

    return serializers.serialize_tenant(session, t)


class TenantCollection(BaseHandler):
    check_roles = 'admin'
    root_tenant_only = True
    invalidate_cache = True

    def get(self):
        """
        Return the list of registered tenants
        """
        return get_tenant_list()

    def post(self):
        """
        Create a new tenant
        """
        request = self.validate_request(self.request.content.read(),
                                        requests.AdminTenantDesc)

        return create_and_initialize(request)


class TenantInstance(BaseHandler):
    check_roles = 'admin'
    root_tenant_only = True
    invalidate_cache = True

    def get(self, tid):
        return get(int(tid))

    def put(self, tid):
        """
        Update the specified tenant.
        """
        request = self.validate_request(self.request.content.read(),
                                        requests.AdminTenantDesc)

        return update(int(tid), request)

    def delete(self, tid):
        """
        Delete the specified tenant.
        """
        return tw(db_del, models.Tenant, models.Tenant.id == int(tid))
