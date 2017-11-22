# -*- coding: UTF-8
#
#   tenant
#   *****
# Implementation of the Tenant handlers
import os

from twisted.internet.defer import returnValue, inlineCallbacks

from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import db_update_defaults, load_appdata
from globaleaks.handlers.admin import files
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.utility import log
from globaleaks.settings import Settings
from globaleaks.state import State


def serialize_tenant(store, tenant):
    return {
        'id': tenant.id,
        'label': tenant.label,
        'active': tenant.active,
        'subdomain': tenant.subdomain,
        'wizard_url': 'http://p{}.{}'.format(tenant.id, State.tenant_cache[1].hostname),
    }


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
            files.db_add_file(store, t.id, f.read(), file_desc[0])

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


@transact
def delete(store, id):
    models.db_delete(store, models.Tenant, models.Tenant.id != 1, id=id)

    db_refresh_memory_variables(store)


def refresh_tenant_states():
    # Remove selected onion services and add missing services
    if State.onion_service_job:
        def f(*args):
            return State.onion_service_job.add_all_hidden_services()

        State.onion_service_job.remove_unwanted_hidden_services().addBoth(f) # pylint: disable=no-member

    # Power cycle HTTPS processes
    def g(*args):
        return State.process_supervisor.maybe_launch_https_workers()

    State.process_supervisor.shutdown(friendly=True).addBoth(g)  # pylint: disable=no-member


class TenantCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True
    root_tenant_only = True

    def get(self):
        """
        Return the list of registered tenants
        """
        return get_tenant_list()

    @inlineCallbacks
    def post(self):
        """
        Create a new tenant
        """
        request = self.validate_message(self.request.content.read(), requests.AdminTenantDesc)

        t = yield create(request)

        refresh_tenant_states()

        returnValue(t)


class TenantInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True
    root_tenant_only = True

    @inlineCallbacks
    def delete(self, tenant_id):
        """
        Delete the specified tenant.
        """
        t = yield delete(int(tenant_id))

        refresh_tenant_states()

        returnValue(t)

    @inlineCallbacks
    def put(self, tenant_id):
        """
        Update the specified tenant.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminTenantDesc)

        yield update(int(tenant_id), request)

        refresh_tenant_states()

        returnValue(None)

    def get(self, tenant_id):
        return get(id=int(tenant_id))
